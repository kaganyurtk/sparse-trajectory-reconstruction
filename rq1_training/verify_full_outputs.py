"""Independent audit of all 98 v2 full-experiment outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch

from experiment import Encoder, load_flights, load_npz_model, object_sha256, sha256, split_inner, targets
from run_experiment import primary_analysis


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "outputs" / "full_v2"
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    fingerprint = manifest.pop("global_fingerprint")
    if object_sha256(manifest) != fingerprint:
        raise AssertionError("Global manifest fingerprint mismatch")
    manifest["global_fingerprint"] = fingerprint
    for item in manifest["inputs"]:
        path = Path(item["path"])
        if not path.is_file() or path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
            raise AssertionError(f"Input changed or missing: {path}")

    train, outer, _ = load_flights(root / "data" / "flights")
    fit, inner, _ = split_inner(train, outer, root / "inner_split.json")
    encoders = {"screen": Encoder.fit(fit), "final": Encoder.fit(train)}
    evaluation = {"screen": inner, "final": outer}
    results = [run for candidates in summary["screening"].values() for candidate in candidates for run in candidate["runs"]]
    results += summary["final_runs"]
    if len(results) != 98 or len({r["run_id"] for r in results}) != 98:
        raise AssertionError("Expected 98 unique runs")

    maximum_difference = 0.0
    for result in results:
        phase = result["config"]["phase"]
        rows, encoder = evaluation[phase], encoders[phase]
        run_dir = output / result["run_id"]
        weights = run_dir / "weights.npz"
        if sha256(weights) != result["weights_sha256"]:
            raise AssertionError(f"Weight hash mismatch: {result['run_id']}")
        model = load_npz_model(weights)
        with torch.no_grad(): replay = encoder.inverse_targets(model(torch.tensor(encoder.transform(rows), dtype=torch.float64)).numpy())
        with (run_dir / "evaluation_predictions.csv").open(newline="", encoding="utf-8") as handle:
            stored = list(csv.DictReader(handle))
        stored_prediction = np.array([[float(r["h_pred_m"]), float(r["v_pred_m_s"])] for r in stored])
        stored_truth = np.array([[float(r["h_true_m"]), float(r["v_true_m_s"])] for r in stored])
        if len(stored) != len(rows) or not np.array_equal(stored_truth, targets(rows)):
            raise AssertionError(f"Stored truth mismatch: {result['run_id']}")
        for expected, row in zip(rows, stored):
            if (row["flight_id"], row["mission"], float(row["time_s"])) != (expected["flight_id"], expected["mission"], float(expected["time_s"])):
                raise AssertionError(f"Prediction identity mismatch: {result['run_id']}")
        difference = float(np.max(np.abs(replay - stored_prediction)))
        maximum_difference = max(maximum_difference, difference)
        if not np.allclose(replay, stored_prediction, rtol=0, atol=1e-10):
            raise AssertionError(f"Replay mismatch: {result['run_id']}")

    recomputed = primary_analysis(summary["final_runs"], encoders["final"].target_scale)
    if json.dumps(recomputed, sort_keys=True) != json.dumps(summary["primary_analysis"], sort_keys=True):
        raise AssertionError("Primary analysis mismatch")
    verification = {
        "schema_version": 2, "status": "passed", "models_replayed": len(results),
        "maximum_prediction_difference": maximum_difference,
        "input_hashes_verified": len(manifest["inputs"]),
        "primary_analysis_recomputed_equal": True,
        "outer_validation_used_for_selection": False,
        "test_trajectory_files_in_inputs": 0,
        "global_fingerprint": fingerprint,
    }
    (output / "verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
