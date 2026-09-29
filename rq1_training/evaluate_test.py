"""One-time evaluation of the 50 frozen final models on the six held-out test flights."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import torch

from experiment import (
    TEST_FLIGHTS, Encoder, flight_metrics, input_manifest, kinematic_loss, load_flights,
    load_npz_model, locked_json, object_sha256, selection_score, sha256, targets, write_predictions,
)
from run_experiment import primary_analysis


def load_test(test_dir: Path):
    rows, sources = [], sorted(test_dir.glob("*.csv"))
    if {p.stem for p in sources} != TEST_FLIGHTS:
        raise ValueError("Test directory must contain exactly the six frozen test flights")
    for path in sources:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            flight = list(csv.DictReader(handle))
        if len(flight) != 121 or {r["partition"] for r in flight} != {"test"} or {r["flight_id"] for r in flight} != {path.stem}:
            raise ValueError(f"Invalid frozen test flight: {path.name}")
        if [float(r["time_s"]) for r in flight] != list(np.arange(121, dtype=float)):
            raise ValueError(f"Unexpected test time grid: {path.name}")
        rows.extend(flight)
    return rows, sources


def secondary(final_results):
    table = []
    for fraction in ("100", "050", "025", "010", "005"):
        entry = {"fraction": fraction}
        for method in ("nn", "kcnn"):
            runs = [r for r in final_results if r["config"]["fraction"] == fraction and r["config"]["method"] == method]
            entry[method] = {
                "h_rmse_m": float(np.mean([r["h_rmse_m"] for r in runs])),
                "v_rmse_m_s": float(np.mean([r["v_rmse_m_s"] for r in runs])),
                "composite": float(np.mean([r["evaluation_score"] for r in runs])),
                "kinematic_violation_fraction": float(np.mean([r["kinematic_violation_fraction"] for r in runs])),
            }
        entry["difference_kcnn_minus_nn"] = entry["kcnn"]["composite"] - entry["nn"]["composite"]
        table.append(entry)
    return table


def main() -> None:
    root = Path(__file__).resolve().parent
    full = root / "outputs" / "full_v2"
    output = root / "outputs" / "test_v2"
    if not (full / "verification.json").is_file():
        raise RuntimeError("Full validation verification is required")
    verification = json.loads((full / "verification.json").read_text(encoding="utf-8"))
    if verification.get("status") != "passed" or verification.get("models_replayed") != 98:
        raise RuntimeError("Full validation verification did not pass")
    full_summary = json.loads((full / "summary.json").read_text(encoding="utf-8"))
    full_manifest = json.loads((full / "run_manifest.json").read_text(encoding="utf-8"))
    train, _, train_sources = load_flights(root / "data" / "flights")
    encoder = Encoder.fit(train)
    if encoder.as_dict() != full_manifest["encoders"]["final"]:
        raise RuntimeError("Frozen final encoder mismatch")
    test_rows, test_sources = load_test(root / "data" / "test_flights")
    x_test = torch.tensor(encoder.transform(test_rows), dtype=torch.float64)
    y_test = targets(test_rows)
    frozen = full_summary["final_runs"]
    if len(frozen) != 50:
        raise RuntimeError("Expected exactly 50 frozen final models")

    source_files = test_sources + [Path(__file__).resolve(), root / "verify_test_outputs.py",
                                   root / "TEST_EVALUATION_PROTOCOL.md", full / "summary.json",
                                   full / "run_manifest.json", full / "verification.json"]
    manifest = {
        "schema_version": 1,
        "status": "frozen_before_test_evaluation",
        "test_flights": sorted(TEST_FLIGHTS),
        "test_rows": len(test_rows),
        "frozen_final_models": len(frozen),
        "encoder": encoder.as_dict(),
        "sources": input_manifest(source_files),
        "model_weights": [{"run_id": r["run_id"], "sha256": r["weights_sha256"]} for r in frozen],
        "training_or_tuning_during_test": False,
    }
    manifest["fingerprint"] = object_sha256(manifest)
    locked_json(output / "test_manifest.json", manifest)

    results = []
    for frozen_result in frozen:
        run_id = frozen_result["run_id"]
        weights = full / run_id / "weights.npz"
        if sha256(weights) != frozen_result["weights_sha256"]:
            raise RuntimeError(f"Frozen weight hash mismatch: {run_id}")
        model = load_npz_model(weights)
        with torch.no_grad(): prediction = encoder.inverse_targets(model(x_test).numpy())
        metrics = flight_metrics(test_rows, y_test, prediction)
        kin_loss, diagnostics = kinematic_loss(model, x_test, encoder.target_mean, encoder.target_scale)
        run_output = output / run_id
        run_output.mkdir(parents=True, exist_ok=True)
        write_predictions(run_output / "test_predictions.csv", test_rows, y_test, prediction)
        result = {
            "run_id": run_id, "config": frozen_result["config"],
            "weights_sha256": frozen_result["weights_sha256"],
            "evaluation_score": selection_score(metrics, encoder.target_scale),
            "h_rmse_m": float(np.mean([m["h_rmse_m"] for m in metrics])),
            "v_rmse_m_s": float(np.mean([m["v_rmse_m_s"] for m in metrics])),
            "kinematic_loss": float(kin_loss.detach()),
            "kinematic_violation_fraction": float(diagnostics["violation"].double().mean().detach()),
            "metrics_per_flight": metrics,
        }
        locked_json(run_output / "result.json", result)
        results.append(result)
    summary = {
        "schema_version": 1, "status": "one_time_test_evaluation_complete",
        "primary_analysis": primary_analysis(results, encoder.target_scale),
        "secondary_by_fraction": secondary(results), "test_results": results,
        "frozen_models_evaluated": 50, "training_or_tuning_during_test": False,
        "test_manifest_fingerprint": manifest["fingerprint"],
    }
    locked_json(output / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "frozen_models_evaluated": 50,
                      "primary_analysis": summary["primary_analysis"]}, indent=2))


if __name__ == "__main__":
    main()
