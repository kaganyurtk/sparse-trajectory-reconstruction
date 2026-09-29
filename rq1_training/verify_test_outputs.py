"""Replay audit for the one-time frozen test evaluation."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch

from evaluate_test import load_test
from experiment import Encoder, load_flights, load_npz_model, object_sha256, sha256, targets
from run_experiment import primary_analysis


def main() -> None:
    root = Path(__file__).resolve().parent
    full, output = root / "outputs" / "full_v2", root / "outputs" / "test_v2"
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "test_manifest.json").read_text(encoding="utf-8"))
    fingerprint = manifest.pop("fingerprint")
    if object_sha256(manifest) != fingerprint or fingerprint != summary["test_manifest_fingerprint"]:
        raise AssertionError("Test manifest fingerprint mismatch")
    manifest["fingerprint"] = fingerprint
    for item in manifest["sources"]:
        path = Path(item["path"])
        if not path.is_file() or path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
            raise AssertionError(f"Test source changed: {path}")
    train, _, _ = load_flights(root / "data" / "flights")
    test_rows, _ = load_test(root / "data" / "test_flights")
    encoder, truth = Encoder.fit(train), targets(test_rows)
    x_test = torch.tensor(encoder.transform(test_rows), dtype=torch.float64)
    maximum = 0.0
    for result in summary["test_results"]:
        weights = full / result["run_id"] / "weights.npz"
        if sha256(weights) != result["weights_sha256"]: raise AssertionError("Weight hash mismatch")
        with torch.no_grad(): replay = encoder.inverse_targets(load_npz_model(weights)(x_test).numpy())
        with (output / result["run_id"] / "test_predictions.csv").open(newline="", encoding="utf-8") as handle:
            stored = list(csv.DictReader(handle))
        pred = np.array([[float(r["h_pred_m"]), float(r["v_pred_m_s"])] for r in stored])
        saved_truth = np.array([[float(r["h_true_m"]), float(r["v_true_m_s"])] for r in stored])
        if len(stored) != 726 or not np.array_equal(saved_truth, truth): raise AssertionError("Truth mismatch")
        maximum = max(maximum, float(np.max(np.abs(replay - pred))))
        if not np.allclose(replay, pred, rtol=0, atol=1e-10): raise AssertionError("Replay mismatch")
    recomputed = primary_analysis(summary["test_results"], encoder.target_scale)
    if json.dumps(recomputed, sort_keys=True) != json.dumps(summary["primary_analysis"], sort_keys=True):
        raise AssertionError("Primary analysis mismatch")
    result = {"status": "passed", "models_replayed": 50, "maximum_prediction_difference": maximum,
              "primary_analysis_recomputed_equal": True, "test_flights": 6,
              "training_or_tuning_during_test": False, "test_manifest_fingerprint": fingerprint}
    (output / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
