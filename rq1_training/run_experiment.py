"""Run the preregistered RQ1 smoke check or full 98-run experiment."""
from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

from experiment import (
    FINAL_SEEDS, FRACTIONS, SCREEN_SEEDS, Encoder, TrainConfig,
    calibrate_kinematic_weight, input_manifest, load_flights, locked_json,
    object_sha256, sha256, split_inner, train_one,
)

GRID = tuple((lr, wd) for lr in (0.0003, 0.001) for wd in (0.0, 0.000001, 0.00001, 0.0001))


def manifest_path(fractions_dir: Path, fraction: str) -> Path:
    return fractions_dir / f"train_{fraction}pct.csv"


def resolve_protocol(root: Path, explicit: Path | None) -> Path:
    candidates = [explicit] if explicit else [root.parent / "RQ1_EXPERIMENT_PROTOCOL.md", root / "RQ1_EXPERIMENT_PROTOCOL.md"]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("RQ1_EXPERIMENT_PROTOCOL.md is required; pass --protocol")


def aggregate(results: list[dict[str, object]]) -> dict[str, float | int]:
    return {
        "n_seeds": len(results),
        "checkpoint_score_mean": float(np.mean([float(r["checkpoint_score"]) for r in results])),
        "best_epoch_median": int(np.median([int(r["best_epoch"]) for r in results])),
    }


def run_fingerprint(global_fingerprint: str, config: TrainConfig, fit_rows, evaluation_rows,
                    encoder: Encoder, mask: Path, checkpoint_rows=None) -> str:
    return object_sha256({
        "global_manifest_fingerprint": global_fingerprint,
        "config": asdict(config),
        "fit_flights": sorted({r["flight_id"] for r in fit_rows}),
        "evaluation_flights": sorted({r["flight_id"] for r in evaluation_rows}),
        "checkpoint_flights": sorted({r["flight_id"] for r in checkpoint_rows or []}),
        "encoder": encoder.as_dict(),
        "mask_sha256": sha256(mask),
    })


def primary_analysis(final_runs: list[dict[str, object]], target_scale, bootstrap_repeats=10_000,
                     bootstrap_seed=20260920) -> dict[str, object]:
    selected = [r for r in final_runs if r["config"]["fraction"] == "005"]
    by_method: dict[str, dict[str, list[float]]] = {"nn": {}, "kcnn": {}}
    for result in selected:
        method = str(result["config"]["method"])
        for metric in result["metrics_per_flight"]:
            value = 0.5 * (float(metric["h_rmse_m"]) / target_scale[0]
                           + float(metric["v_rmse_m_s"]) / target_scale[1])
            by_method[method].setdefault(str(metric["flight_id"]), []).append(value)
    if set(by_method["nn"]) != set(by_method["kcnn"]) or len(by_method["nn"]) != 6:
        raise ValueError("Primary analysis requires the same six outer-validation flights")
    records, differences = [], []
    for flight_id in sorted(by_method["nn"]):
        if len(by_method["nn"][flight_id]) != 5 or len(by_method["kcnn"][flight_id]) != 5:
            raise ValueError("Primary analysis requires five seeds per method and flight")
        nn_value = float(np.mean(by_method["nn"][flight_id]))
        kcnn_value = float(np.mean(by_method["kcnn"][flight_id]))
        difference = kcnn_value - nn_value
        differences.append(difference)
        records.append({"flight_id": flight_id, "nn_seed_mean": nn_value,
                        "kcnn_seed_mean": kcnn_value, "difference_kcnn_minus_nn": difference})
    values = np.asarray(differences)
    rng = np.random.default_rng(bootstrap_seed)
    boot = values[rng.integers(0, len(values), size=(bootstrap_repeats, len(values)))].mean(axis=1)
    return {
        "estimand": "fraction 005 outer-validation flight-macro standardized composite difference, KC-NN minus NN",
        "negative_favors": "kcnn",
        "flight_records": records,
        "mean_difference": float(values.mean()),
        "median_difference": float(np.median(values)),
        "flights_favoring_kcnn": int(np.sum(values < 0)),
        "n_flights": len(values),
        "bootstrap": {"unit": "flight", "repeats": bootstrap_repeats, "seed": bootstrap_seed,
                      "ci_95_percentile": [float(x) for x in np.quantile(boot, [0.025, 0.975])]},
    }


def run(root: Path, mode: str, smoke_epochs: int, data_root: Path | None = None,
        protocol_path: Path | None = None) -> dict[str, object]:
    data = data_root or root / "data"
    flights_dir, fractions_dir = data / "flights", data / "fractions"
    protocol = resolve_protocol(root, protocol_path)
    split_path = root / "inner_split.json"
    train, outer_validation, sources = load_flights(flights_dir)
    inner_fit, inner_validation, split = split_inner(train, outer_validation, split_path)
    encoder_inner, encoder_final = Encoder.fit(inner_fit), Encoder.fit(train)
    masks = [manifest_path(fractions_dir, fraction) for fraction in FRACTIONS]
    all_inputs = sources + masks + [protocol, split_path, Path(__file__).resolve(), root / "experiment.py",
                                    root / "requirements.txt", data / "flight_metadata.csv"]
    out = root / "outputs" / ("smoke_v2" if mode == "smoke" else "full_v2")
    manifest = {
        "schema_version": 2, "mode": mode, "python": platform.python_version(),
        "numpy": np.__version__, "torch": torch.__version__,
        "partitions": {"inner_fit_flights": 22, "inner_validation_flights": 6,
                       "outer_validation_flights": 6, "test_trajectory_files_in_inputs": 0},
        "inner_split": split,
        "encoders": {"inner": encoder_inner.as_dict(), "final": encoder_final.as_dict()},
        "inputs": input_manifest(all_inputs),
    }
    manifest["global_fingerprint"] = object_sha256(manifest)
    locked_json(out / "run_manifest.json", manifest)
    lambda_record = calibrate_kinematic_weight(inner_fit, encoder_inner, manifest_path(fractions_dir, "100"))
    locked_json(out / "kinematic_weight_calibration.json", lambda_record)
    kinematic_weight = float(lambda_record["kinematic_weight"])

    if mode == "smoke":
        results = []
        mask = manifest_path(fractions_dir, "005")
        for method in ("nn", "kcnn"):
            config = TrainConfig(method, "smoke", "005", 11, 0.001, 0.0001,
                                 max_epochs=smoke_epochs, checkpoint_interval=1,
                                 stale_checks=smoke_epochs + 1)
            fingerprint = run_fingerprint(manifest["global_fingerprint"], config, inner_fit,
                                          inner_validation, encoder_inner, mask, inner_validation)
            results.append(train_one(config, inner_fit, inner_validation, encoder_inner, mask,
                                     out / config.run_id, fingerprint, kinematic_weight, inner_validation))
        summary = {
            "schema_version": 2, "status": "smoke_only_not_scientific_result", "runs": results,
            "kinematic_weight": kinematic_weight,
            "paired_initialization_equal": results[0]["initialization_sha256"] == results[1]["initialization_sha256"],
            "outer_validation_used_for_selection": False,
            "test_trajectory_files_in_inputs": 0,
        }
        locked_json(out / "summary.json", summary)
        return summary

    screening: dict[str, list[dict[str, object]]] = {"nn": [], "kcnn": []}
    winners: dict[str, dict[str, float | int]] = {}
    screen_mask = manifest_path(fractions_dir, "100")
    for method in ("nn", "kcnn"):
        candidates = []
        for lr, wd in GRID:
            runs = []
            for seed in SCREEN_SEEDS:
                config = TrainConfig(method, "screen", "100", seed, lr, wd, max_epochs=1000)
                fingerprint = run_fingerprint(manifest["global_fingerprint"], config, inner_fit,
                                              inner_validation, encoder_inner, screen_mask, inner_validation)
                runs.append(train_one(config, inner_fit, inner_validation, encoder_inner, screen_mask,
                                      out / config.run_id, fingerprint, kinematic_weight, inner_validation))
            candidates.append({"method": method, "learning_rate": lr, "weight_decay": wd,
                               "runs": runs, **aggregate(runs)})
        candidates.sort(key=lambda item: (item["checkpoint_score_mean"], -item["weight_decay"], item["learning_rate"]))
        screening[method] = candidates
        winner = candidates[0]
        winners[method] = {"learning_rate": float(winner["learning_rate"]),
                           "weight_decay": float(winner["weight_decay"]),
                           "final_epochs": int(winner["best_epoch_median"])}

    final_runs: list[dict[str, object]] = []
    for fraction in FRACTIONS:
        mask = manifest_path(fractions_dir, fraction)
        for method in ("nn", "kcnn"):
            winner = winners[method]
            for seed in FINAL_SEEDS:
                config = TrainConfig(method, "final", fraction, seed,
                                     float(winner["learning_rate"]), float(winner["weight_decay"]),
                                     max_epochs=int(winner["final_epochs"]))
                fingerprint = run_fingerprint(manifest["global_fingerprint"], config, train,
                                              outer_validation, encoder_final, mask)
                final_runs.append(train_one(config, train, outer_validation, encoder_final, mask,
                                            out / config.run_id, fingerprint, kinematic_weight))
    summary = {
        "schema_version": 2, "status": "full_validation_complete_test_still_closed",
        "screening": screening, "winners": winners, "final_runs": final_runs,
        "primary_analysis": primary_analysis(final_runs, encoder_final.target_scale),
        "planned_and_completed_unique_runs": 98,
        "outer_validation_used_for_selection": False,
        "test_trajectory_files_in_inputs": 0,
    }
    locked_json(out / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--protocol", type=Path)
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--smoke-epochs", type=int, default=5)
    args = parser.parse_args()
    result = run(args.root.resolve(), args.mode, args.smoke_epochs,
                 args.data_root.resolve() if args.data_root else None,
                 args.protocol.resolve() if args.protocol else None)
    print(json.dumps({"mode": args.mode, "status": result["status"]}, indent=2))


if __name__ == "__main__":
    main()
