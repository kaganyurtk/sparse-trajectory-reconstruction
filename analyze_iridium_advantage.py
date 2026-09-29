#!/usr/bin/env python3
"""Post-hoc diagnostic of the KC-NN advantage on Iridium NEXT-5.

This script only reads frozen RQ1 outputs. It performs no training or tuning.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "iridium_diagnostic.json"
REPORT = ROOT / "IRIDIUM_NEXT5_DIAGNOSTIC.md"
FIGURES = ROOT / "figures"
FLIGHT = "iridium_next_5"
METHODS = ("nn", "kcnn")
FRACTIONS = ("100", "050", "025", "010", "005")


def result_files(method: str, fraction: str):
    return sorted((ROOT / "outputs" / "test_v2").glob(f"final_{method}_f{fraction}_*/result.json"))


def flight_metric(result: dict) -> dict:
    return next(row for row in result["metrics_per_flight"] if row["flight_id"] == FLIGHT)


def seed_metrics(h_scale: float, v_scale: float):
    rows = []
    for method in METHODS:
        for path in result_files(method, "005"):
            result = json.loads(path.read_text(encoding="utf-8"))
            metric = flight_metric(result)
            rows.append(
                {
                    "method": method,
                    "seed": result["config"]["seed"],
                    "h_rmse_m": metric["h_rmse_m"],
                    "v_rmse_m_s": metric["v_rmse_m_s"],
                    "composite": 0.5
                    * (metric["h_rmse_m"] / h_scale + metric["v_rmse_m_s"] / v_scale),
                }
            )
    return pd.DataFrame(rows)


def prediction_ensembles():
    ensembles = {}
    raw = {}
    for method in METHODS:
        frames = []
        pattern = f"final_{method}_f005_*/test_predictions.csv"
        for path in sorted((ROOT / "outputs" / "test_v2").glob(pattern)):
            frame = pd.read_csv(path)
            frame = frame.loc[frame.flight_id == FLIGHT].copy()
            frame["seed"] = int(path.parent.name.split("_seed")[1].split("_")[0])
            frames.append(frame)
        raw[method] = pd.concat(frames, ignore_index=True)
        ensembles[method] = (
            raw[method]
            .groupby("time_s", as_index=False)
            .agg(
                h_true_m=("h_true_m", "first"),
                v_true_m_s=("v_true_m_s", "first"),
                h_pred_m=("h_pred_m", "mean"),
                v_pred_m_s=("v_pred_m_s", "mean"),
                h_pred_sd=("h_pred_m", "std"),
                v_pred_sd=("v_pred_m_s", "std"),
            )
        )
    return ensembles, raw


def window_metrics(ensembles: dict):
    windows = ((0, 30), (31, 60), (61, 90), (91, 120))
    rows = []
    for method, frame in ensembles.items():
        for lo, hi in windows:
            part = frame.loc[frame.time_s.between(lo, hi)]
            h_error = part.h_pred_m - part.h_true_m
            v_error = part.v_pred_m_s - part.v_true_m_s
            rows.append(
                {
                    "method": method,
                    "window_s": f"{lo}-{hi}",
                    "h_rmse_m_ensemble": float(np.sqrt(np.mean(h_error**2))),
                    "v_rmse_m_s_ensemble": float(np.sqrt(np.mean(v_error**2))),
                    "h_bias_m_ensemble": float(np.mean(h_error)),
                    "v_bias_m_s_ensemble": float(np.mean(v_error)),
                }
            )
    return rows


def fraction_metrics(h_scale: float, v_scale: float):
    rows = []
    for fraction in FRACTIONS:
        values = {}
        for method in METHODS:
            scores = []
            for path in result_files(method, fraction):
                metric = flight_metric(json.loads(path.read_text(encoding="utf-8")))
                scores.append(
                    0.5 * (metric["h_rmse_m"] / h_scale + metric["v_rmse_m_s"] / v_scale)
                )
            values[method] = float(np.mean(scores))
        rows.append(
            {
                "fraction": fraction,
                "nn": values["nn"],
                "kcnn": values["kcnn"],
                "difference_kcnn_minus_nn": values["kcnn"] - values["nn"],
            }
        )
    return rows


def static_feature_neighbors(manifest: dict):
    with (ROOT / "data" / "flight_metadata.csv").open(encoding="utf-8") as handle:
        metadata = list(csv.DictReader(handle))
    target = next(row for row in metadata if row["flight_id"] == FLIGHT)
    median = manifest["encoder"]["payload_median"]
    std = manifest["encoder"]["payload_std"]

    def payload(row):
        return float(row["payload_kg"]) if row["payload_kg"] else median

    def distance(row):
        payload_delta = (payload(row) - float(target["payload_kg"])) / std
        block_delta = 0.0 if row["block"] == target["block"] else np.sqrt(2.0)
        missing_delta = 0.0 if row["payload_kg"] else 1.0
        return float(np.sqrt(payload_delta**2 + block_delta**2 + missing_delta**2))

    neighbors = []
    for row in sorted((r for r in metadata if r["partition"] == "train"), key=distance)[:8]:
        neighbors.append(
            {
                "flight_id": row["flight_id"],
                "mission": row["mission"],
                "block": row["block"],
                "payload_kg": None if not row["payload_kg"] else float(row["payload_kg"]),
                "orbit_not_used_by_model": row["orbit"],
                "encoded_static_distance": distance(row),
            }
        )
    return neighbors


def approximate_violation(frame: pd.DataFrame):
    vertical_rate = np.gradient(frame.h_pred_m.to_numpy(), frame.time_s.to_numpy())
    speed = frame.v_pred_m_s.to_numpy()
    return float(np.mean((vertical_rate < 0) | (vertical_rate > speed)))


def make_figures(ensembles: dict, fraction_rows: list[dict]):
    FIGURES.mkdir(exist_ok=True)
    truth = ensembles["nn"]
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
    axes[0].plot(truth.time_s, truth.h_true_m / 1000, color="black", lw=2.5, label="Truth")
    axes[1].plot(truth.time_s, truth.v_true_m_s, color="black", lw=2.5, label="Truth")
    labels = {"nn": "NN", "kcnn": "KC-NN"}
    colors = {"nn": "#d95f02", "kcnn": "#1b9e77"}
    for method, frame in ensembles.items():
        axes[0].plot(frame.time_s, frame.h_pred_m / 1000, lw=2, color=colors[method], label=labels[method])
        axes[0].fill_between(
            frame.time_s,
            (frame.h_pred_m - frame.h_pred_sd) / 1000,
            (frame.h_pred_m + frame.h_pred_sd) / 1000,
            color=colors[method], alpha=0.14,
        )
        axes[1].plot(frame.time_s, frame.v_pred_m_s, lw=2, color=colors[method], label=labels[method])
        axes[1].fill_between(
            frame.time_s,
            frame.v_pred_m_s - frame.v_pred_sd,
            frame.v_pred_m_s + frame.v_pred_sd,
            color=colors[method], alpha=0.14,
        )
    axes[0].set_ylabel("Altitude (km)")
    axes[1].set_ylabel("Speed (m/s)")
    axes[1].set_xlabel("Time after launch (s)")
    axes[0].set_title("Iridium NEXT-5 at 5% training observations")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, ncol=3)
    fig.savefig(FIGURES / "figure_6_iridium_next5_trajectories.png", dpi=220)
    fig.savefig(FIGURES / "figure_6_iridium_next5_trajectories.pdf")
    plt.close(fig)

    frac = pd.DataFrame(fraction_rows)
    x = np.arange(len(frac))
    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    ax.plot(x, frac.nn, marker="o", lw=2, label="NN", color=colors["nn"])
    ax.plot(x, frac.kcnn, marker="o", lw=2, label="KC-NN", color=colors["kcnn"])
    ax.set_xticks(x, ["100%", "50%", "25%", "10%", "5%"])
    ax.set_xlabel("Training observations retained")
    ax.set_ylabel("Standardized composite error")
    ax.set_title("Iridium NEXT-5 advantage persists at every observation rate")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.savefig(FIGURES / "figure_7_iridium_next5_by_fraction.png", dpi=220)
    fig.savefig(FIGURES / "figure_7_iridium_next5_by_fraction.pdf")
    plt.close(fig)


def main():
    manifest = json.loads((ROOT / "outputs" / "test_v2" / "test_manifest.json").read_text())
    h_scale, v_scale = manifest["encoder"]["target_scale"]
    seeds = seed_metrics(h_scale, v_scale)
    ensembles, _ = prediction_ensembles()
    fractions = fraction_metrics(h_scale, v_scale)
    windows = window_metrics(ensembles)
    neighbors = static_feature_neighbors(manifest)

    means = seeds.groupby("method")[["h_rmse_m", "v_rmse_m_s", "composite"]].mean()
    h_gain = 0.5 * (means.loc["nn", "h_rmse_m"] - means.loc["kcnn", "h_rmse_m"]) / h_scale
    v_gain = 0.5 * (means.loc["nn", "v_rmse_m_s"] - means.loc["kcnn", "v_rmse_m_s"]) / v_scale
    total_gain = h_gain + v_gain
    paired = seeds.pivot(index="seed", columns="method", values=["h_rmse_m", "v_rmse_m_s", "composite"])

    payload = {
        "scope": "post_hoc_frozen_outputs_only_no_training_or_tuning",
        "flight_id": FLIGHT,
        "fraction_005_seed_means": means.to_dict(orient="index"),
        "fraction_005_gain_decomposition": {
            "nn_minus_kcnn_composite": float(total_gain),
            "altitude_component": float(h_gain),
            "speed_component": float(v_gain),
            "altitude_share_percent": float(100 * h_gain / total_gain),
        },
        "paired_seed_records": seeds.sort_values(["seed", "method"]).to_dict(orient="records"),
        "kcnn_better_composite_seed_count": int((paired["composite", "kcnn"] < paired["composite", "nn"]).sum()),
        "kcnn_better_altitude_seed_count": int((paired["h_rmse_m", "kcnn"] < paired["h_rmse_m", "nn"]).sum()),
        "kcnn_better_speed_seed_count": int((paired["v_rmse_m_s", "kcnn"] < paired["v_rmse_m_s", "nn"]).sum()),
        "time_window_ensemble_metrics": windows,
        "fraction_sensitivity": fractions,
        "nearest_training_flights_in_model_static_feature_space": neighbors,
        "ensemble_finite_difference_violation_fraction": {
            method: approximate_violation(frame) for method, frame in ensembles.items()
        },
        "interpretation": {
            "supported": [
                "The advantage is seed-consistent and present at all five observation rates.",
                "Most of the 5% composite gain comes from reduced altitude error.",
                "NN overshoots altitude through much of the middle and late trajectory; KC-NN reduces that overshoot.",
                "The physical penalty strongly reduces approximate prediction-trajectory inequality violations.",
            ],
            "plausible_not_causal": (
                "KC-NN acts as a regularizer for the high-payload Block-4 feature combination, "
                "which is only sparsely represented in training."
            ),
            "caveat": (
                "The constraint is an inequality using total speed, not an exact vertical-velocity equation; "
                "finite-difference diagnostics are also affected by quantized altitude telemetry."
            ),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    frac_lines = "\n".join(
        f"| {int(r['fraction'])}% | {r['nn']:.4f} | {r['kcnn']:.4f} | {r['difference_kcnn_minus_nn']:+.4f} |"
        for r in fractions
    )
    report = f"""# Iridium NEXT-5 KC-NN diagnostic

This is a post-hoc read-only analysis of frozen RQ1 outputs. No model was trained or tuned.

## Main finding

At 5% observations, mean composite error is {means.loc['nn', 'composite']:.4f} for NN and
{means.loc['kcnn', 'composite']:.4f} for KC-NN. KC-NN is better for all five paired seeds.
About {100*h_gain/total_gain:.1f}% of the composite improvement comes from altitude RMSE:
the five-seed mean falls from {means.loc['nn', 'h_rmse_m']:.1f} m to
{means.loc['kcnn', 'h_rmse_m']:.1f} m. Speed RMSE falls more modestly from
{means.loc['nn', 'v_rmse_m_s']:.2f} to {means.loc['kcnn', 'v_rmse_m_s']:.2f} m/s and improves
for four of five seeds.

The seed-mean NN trajectory overshoots the true altitude after roughly 30 s, with its largest
error in the 61–90 s window. KC-NN substantially suppresses that overshoot. Its approximate
finite-difference inequality-violation fraction is
{payload['ensemble_finite_difference_violation_fraction']['kcnn']:.1%}, versus
{payload['ensemble_finite_difference_violation_fraction']['nn']:.1%} for NN.

## Observation-rate sensitivity

| Training observations | NN | KC-NN | KC-NN minus NN |
|---:|---:|---:|---:|
{frac_lines}

The advantage exists even at 100% and grows as training becomes sparser. It is therefore not
specific to one 5% mask.

## Most plausible explanation

The network input does not include mission identity or orbit. Iridium NEXT-5 appears only as
time + Block 4 + 9,600 kg payload. Its closest training point in that encoded static feature
space is Iridium NEXT-3 (Block 4, 8,600 kg); the exact Block-4/9,600-kg combination is absent.
The unconstrained NN extrapolates this combination into an overly high middle/late altitude
curve. The inequality penalty behaves like a trajectory-shape regularizer and prevents most
of that overshoot. This mechanism is strongly supported descriptively, but it is not a causal
proof because the post-hoc analysis does not intervene on individual constraint terms.

## Important caveat

The KC-NN penalty enforces `0 <= dh/dt <= total speed` and nonnegative speed. Total speed is
not vertical speed, so this is a weak plausibility inequality rather than an exact kinematic
equation. Altitude telemetry is quantized, which also makes pointwise finite differences noisy.
"""
    REPORT.write_text(report, encoding="utf-8")
    make_figures(ensembles, fractions)
    print(json.dumps(payload["fraction_005_gain_decomposition"], indent=2))


if __name__ == "__main__":
    main()
