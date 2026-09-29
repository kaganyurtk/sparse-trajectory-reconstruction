"""Independent replay and audit checks for v2 smoke outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch

from experiment import Encoder, load_flights, load_npz_model, sha256, split_inner, targets


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "outputs" / "smoke_v2"
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    train, outer, _ = load_flights(root / "data" / "flights")
    fit, inner, _ = split_inner(train, outer, root / "inner_split.json")
    encoder = Encoder.fit(fit)
    x_eval = torch.tensor(encoder.transform(inner), dtype=torch.float64)
    truth = targets(inner)
    maximum_difference, checked = 0.0, 0
    for result in summary["runs"]:
        run_dir = output / result["run_id"]
        weights = run_dir / "weights.npz"
        if result["weights_sha256"] != sha256(weights):
            raise AssertionError(f"Weight hash mismatch: {result['run_id']}")
        model = load_npz_model(weights)
        with torch.no_grad(): replay = encoder.inverse_targets(model(x_eval).numpy())
        with (run_dir / "evaluation_predictions.csv").open(newline="", encoding="utf-8") as handle:
            stored = list(csv.DictReader(handle))
        if len(stored) != len(inner): raise AssertionError("Prediction row count mismatch")
        stored_prediction = np.array([[float(r["h_pred_m"]), float(r["v_pred_m_s"])] for r in stored])
        stored_truth = np.array([[float(r["h_true_m"]), float(r["v_true_m_s"])] for r in stored])
        for expected, row in zip(inner, stored):
            if (row["flight_id"], row["mission"], float(row["time_s"])) != (expected["flight_id"], expected["mission"], float(expected["time_s"])):
                raise AssertionError("Prediction identity mismatch")
        difference = float(np.max(np.abs(replay - stored_prediction)))
        maximum_difference = max(maximum_difference, difference)
        if not np.allclose(replay, stored_prediction, rtol=0, atol=1e-10):
            raise AssertionError(f"Replay mismatch: {result['run_id']}")
        if not np.array_equal(truth, stored_truth): raise AssertionError("Stored truth mismatch")
        checked += 1
    verification = {
        "schema_version": 2, "status": "passed", "models_replayed": checked,
        "maximum_prediction_difference": maximum_difference,
        "paired_initialization_equal": bool(summary["paired_initialization_equal"]),
        "inner_fit_flights": len({r["flight_id"] for r in fit}),
        "inner_validation_flights": len({r["flight_id"] for r in inner}),
        "outer_validation_loaded_but_not_evaluated_in_smoke": len({r["flight_id"] for r in outer}),
        "outer_validation_used_for_selection": False,
        "global_fingerprint": manifest["global_fingerprint"],
        "test_trajectory_files_in_inputs": 0,
    }
    path = output / "verification.json"
    path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
