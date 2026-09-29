#!/usr/bin/env python3
"""Verify the post-hoc kinematic-term ablation and create its report/figure."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiment import object_sha256, sha256


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "kinematic_term_ablation"
SUMMARY_PATH = OUT / "summary.json"
REPORT_PATH = ROOT / "KINEMATIC_TERM_ABLATION_REPORT.md"
VERIFY_PATH = OUT / "verification.json"
FIGURE_PNG = ROOT / "figures" / "figure_8_kinematic_term_ablation.png"
FIGURE_PDF = ROOT / "figures" / "figure_8_kinematic_term_ablation.pdf"


def main():
    summary = json.loads(SUMMARY_PATH.read_text())
    manifest = json.loads((OUT / "manifest.json").read_text())
    fingerprint_body = dict(manifest)
    observed_fingerprint = fingerprint_body.pop("fingerprint")
    checks = {
        "summary_status": summary["status"] == "post_hoc_kinematic_term_ablation_complete",
        "manifest_fingerprint": object_sha256(fingerprint_body) == observed_fingerprint,
        "planned_and_completed_runs": summary["planned_runs"] == summary["completed_runs"] == 15,
        "variant_count": len(summary["variants"]) == 3,
        "seed_count_per_variant": all(
            len(value["iridium_seed_records"]) == 5 for value in summary["variants"].values()
        ),
    }
    expected = {(variant, seed) for variant in summary["variants"] for seed in (11, 29, 47, 71, 97)}
    observed = set()
    prediction_rows_ok = True
    hashes_ok = True
    finite_ok = True
    for variant, seed in sorted(expected):
        run_dir = OUT / variant / f"seed_{seed}"
        result = json.loads((run_dir / "result.json").read_text())
        test_result = json.loads((run_dir / "test_result.json").read_text())
        observed.add((test_result["variant"], test_result["seed"]))
        hashes_ok &= sha256(run_dir / "weights.npz") == result["weights_sha256"] == test_result["weights_sha256"]
        lines = (run_dir / "test_predictions.csv").read_text().splitlines()
        prediction_rows_ok &= len(lines) == 727
        finite_ok &= all(
            np.isfinite(value)
            for value in (
                test_result["test_evaluation_score"],
                test_result["validation_evaluation_score"],
            )
        )
    checks.update(
        {
            "all_expected_variant_seed_pairs": observed == expected,
            "weights_hashes": bool(hashes_ok),
            "test_prediction_row_counts": bool(prediction_rows_ok),
            "finite_scores": bool(finite_ok),
        }
    )

    # Removing the inactive nonnegative-speed term should be numerically equivalent to full KC-NN.
    full = json.loads((ROOT / "outputs" / "full_v2" / "summary.json").read_text())
    max_parameter_difference = 0.0
    for seed in (11, 29, 47, 71, 97):
        full_path = ROOT / "outputs" / "full_v2" / f"final_kcnn_f005_seed{seed}_lr0.001_wd0.0001_e400" / "weights.npz"
        ablated_path = OUT / "omit_speed_nonnegative" / f"seed_{seed}" / "weights.npz"
        with np.load(full_path, allow_pickle=False) as left, np.load(ablated_path, allow_pickle=False) as right:
            max_parameter_difference = max(
                max_parameter_difference,
                max(float(np.max(np.abs(left[name] - right[name]))) for name in left.files),
            )
    checks["omit_speed_matches_full_within_3e_15"] = max_parameter_difference < 3e-15
    status = "passed" if all(checks.values()) else "failed"
    verification = {
        "status": status,
        "checks": checks,
        "verified_runs": len(observed),
        "max_abs_parameter_difference_omit_speed_vs_full_kcnn": max_parameter_difference,
    }
    VERIFY_PATH.write_text(json.dumps(verification, indent=2) + "\n")
    if status != "passed":
        raise RuntimeError(verification)

    comparators = summary["comparators"]
    values = {
        "NN": comparators["nn"]["seed_mean"]["composite"],
        "Full KC-NN": comparators["kcnn"]["seed_mean"]["composite"],
        "Omit dh/dt >= 0": summary["variants"]["omit_vertical_rate_nonnegative"]["iridium_seed_mean"]["composite"],
        "Omit dh/dt <= speed": summary["variants"]["omit_vertical_rate_le_speed"]["iridium_seed_mean"]["composite"],
        "Omit speed >= 0": summary["variants"]["omit_speed_nonnegative"]["iridium_seed_mean"]["composite"],
    }
    seed_sets = {
        "NN": [row["composite"] for row in comparators["nn"]["seed_records"]],
        "Full KC-NN": [row["composite"] for row in comparators["kcnn"]["seed_records"]],
        "Omit dh/dt >= 0": [row["composite"] for row in summary["variants"]["omit_vertical_rate_nonnegative"]["iridium_seed_records"]],
        "Omit dh/dt <= speed": [row["composite"] for row in summary["variants"]["omit_vertical_rate_le_speed"]["iridium_seed_records"]],
        "Omit speed >= 0": [row["composite"] for row in summary["variants"]["omit_speed_nonnegative"]["iridium_seed_records"]],
    }
    labels = list(values)
    means = np.array([values[label] for label in labels])
    errors = np.array([np.std(seed_sets[label], ddof=1) for label in labels])
    colors = ["#d95f02", "#1b9e77", "#66c2a5", "#c62828", "#80cdc1"]
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, means, xerr=errors, color=colors, alpha=0.9, capsize=4)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Iridium NEXT-5 standardized composite error (lower is better)")
    ax.set_title("The dh/dt <= speed term drives the KC-NN advantage")
    ax.grid(axis="x", alpha=0.25)
    for index, mean in enumerate(means):
        ax.text(mean + 0.005, index, f"{mean:.3f}", va="center")
    FIGURE_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(FIGURE_PNG, dpi=220)
    fig.savefig(FIGURE_PDF)
    plt.close(fig)

    full_score = values["Full KC-NN"]
    omit_high = values["Omit dh/dt <= speed"]
    omit_low = values["Omit dh/dt >= 0"]
    omit_speed = values["Omit speed >= 0"]
    report = f"""# Kinematic-term ablation report

## Scope

Exploratory post-hoc mechanism analysis using the frozen 5% mask, five paired seeds, the same
32x32 tanh architecture, learning rate, weight decay, 400-epoch budget, and unchanged
kinematic weight. Fifteen planned ablation runs completed; verification passed. This does not
replace the preregistered RQ1 result.

## Iridium NEXT-5 result

| Model / ablation | Five-seed composite | Change vs full KC-NN |
|---|---:|---:|
| NN | {values['NN']:.4f} | {values['NN']-full_score:+.4f} |
| Full KC-NN | {full_score:.4f} | +0.0000 |
| Remove `dh/dt >= 0` | {omit_low:.4f} | {omit_low-full_score:+.4f} |
| Remove `dh/dt <= speed` | {omit_high:.4f} | {omit_high-full_score:+.4f} |
| Remove `speed >= 0` | {omit_speed:.4f} | {omit_speed-full_score:+.4f} |

## Interpretation

The `dh/dt <= speed` hinge is the decisive term. Removing it raises Iridium composite error
from {full_score:.4f} to {omit_high:.4f}, which is also worse than the NN value of
{values['NN']:.4f}. All five seeds deteriorate. This term therefore explains the observed
KC-NN advantage far more strongly than the other two terms.

Removing `speed >= 0` changes the Iridium score by only {omit_speed-full_score:+.3e}; the
resulting parameters match full KC-NN within {max_parameter_difference:.3e} absolute error.
The term was inactive in these runs. Removing `dh/dt >= 0` slightly improves the Iridium mean
to {omit_low:.4f}; it is not responsible for the advantage and may add mild optimization cost
for this flight.

The conclusion remains mechanistic and post-hoc: `speed` is total speed, not vertical speed,
so `dh/dt <= speed` is a plausibility bound rather than an exact dynamical equation.
"""
    REPORT_PATH.write_text(report)
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
