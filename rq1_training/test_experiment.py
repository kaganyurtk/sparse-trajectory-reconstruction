from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import numpy as np
import torch

from experiment import (
    FINAL_SEEDS, SCREEN_SEEDS, Encoder, TrajectoryNet, calibrate_kinematic_weight,
    kinematic_loss, load_flights, locked_json, make_model, objective, observed_rows, split_inner,
)
from run_experiment import GRID, primary_analysis

ROOT = Path(__file__).resolve().parent


def partitions():
    train, outer, sources = load_flights(ROOT / "data" / "flights")
    fit, inner, split = split_inner(train, outer, ROOT / "inner_split.json")
    return train, fit, inner, outer, sources, split


def test_dataset_and_inner_outer_split() -> None:
    train, fit, inner, outer, sources, _ = partitions()
    assert (len(train), len(fit), len(inner), len(outer), len(sources)) == (3388, 2662, 726, 726, 34)
    assert len({r["flight_id"] for r in fit}) == 22
    assert len({r["flight_id"] for r in inner}) == len({r["flight_id"] for r in outer}) == 6
    assert not ({r["flight_id"] for r in fit} & {r["flight_id"] for r in inner})


def test_fraction_sizes_and_nestedness() -> None:
    expected = {"100": 3388, "050": 1680, "025": 840, "010": 336, "005": 168}
    sets = {}
    for fraction, size in expected.items():
        with (ROOT / "data" / "fractions" / f"train_{fraction}pct.csv").open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        sets[fraction] = {(r["flight_id"], float(r["time_s"])) for r in rows}
        assert len(sets[fraction]) == size
    assert sets["005"] <= sets["010"] <= sets["025"] <= sets["050"] <= sets["100"]


def test_final_encoder_matches_frozen_reference() -> None:
    train, *_ = partitions()
    encoder = Encoder.fit(train)
    assert len(encoder.feature_names) == 8
    assert np.isclose(encoder.payload_median, 3875.0)
    assert np.isclose(encoder.payload_std, 2625.587036321507)
    assert np.allclose(encoder.target_mean, [11329.110943607404, 386.4163469752503])
    assert np.allclose(encoder.target_scale, [11092.184987130366, 321.19488580866084])


def test_paired_initialization_is_identical() -> None:
    for pa, pb in zip(make_model(11).parameters(), make_model(11).parameters()):
        assert torch.equal(pa, pb)


def test_chain_rule_and_valid_constraint() -> None:
    model = TrajectoryNet()
    model.forward = lambda x: torch.stack((x[:, 0], torch.zeros_like(x[:, 0])), dim=1)  # type: ignore[method-assign]
    loss, diagnostics = kinematic_loss(model, torch.zeros((4, 8), dtype=torch.float64), (0.0, 100.0), (1200.0, 10.0))
    assert torch.allclose(diagnostics["vertical_rate"], torch.full((4,), 10.0, dtype=torch.float64))
    assert torch.allclose(diagnostics["speed"], torch.full((4,), 100.0, dtype=torch.float64))
    assert float(loss) == 0.0


def test_autograd_derivative_matches_finite_difference() -> None:
    model = make_model(29)
    x = torch.zeros((1, 8), dtype=torch.float64, requires_grad=True); x.data[0, 0] = 0.43
    analytic = torch.autograd.grad(model(x)[0, 0], x)[0][0, 0].item()
    epsilon = 1e-6
    plus, minus = x.detach().clone(), x.detach().clone()
    plus[0, 0] += epsilon; minus[0, 0] -= epsilon
    finite = ((model(plus)[0, 0] - model(minus)[0, 0]) / (2 * epsilon)).item()
    assert np.isclose(analytic, finite, rtol=1e-6, atol=1e-8)


def test_zero_kinematic_weight_matches_nn_update() -> None:
    train, *_ = partitions(); encoder = Encoder.fit(train); rows = train[:16]
    x = torch.tensor(encoder.transform(rows), dtype=torch.float64)
    y = torch.tensor(encoder.standardize_targets(np.array([[float(r["altitude_m"]), float(r["speed_m_s"])] for r in rows])), dtype=torch.float64)
    a, b = make_model(47), make_model(47)
    for model in (a, b):
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001); optimizer.zero_grad(set_to_none=True)
        loss, _, _ = objective(model, x, y, x, encoder, 0.0); loss.backward(); optimizer.step()
    for pa, pb in zip(a.parameters(), b.parameters()): assert torch.equal(pa, pb)


def test_test_file_is_refused() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "ses_9.csv"
        source = ROOT / "data" / "flights" / "abs_2a.csv"
        target.write_text(source.read_text(encoding="utf-8").replace(",train,", ",test,").replace("abs_2a", "ses_9"), encoding="utf-8")
        try: load_flights(Path(directory))
        except RuntimeError as exc: assert "Test trajectory input refused" in str(exc)
        else: raise AssertionError("test trajectory was not refused")


def test_sparse_targets_only_use_fit_partition() -> None:
    _, fit, inner, _, _, _ = partitions()
    selected = observed_rows(fit, ROOT / "data" / "fractions" / "train_005pct.csv")
    assert selected and {r["flight_id"] for r in selected} <= {r["flight_id"] for r in fit}
    assert not ({r["flight_id"] for r in selected} & {r["flight_id"] for r in inner})


def test_train_only_gradient_calibration_is_finite() -> None:
    _, fit, *_ = partitions(); encoder = Encoder.fit(fit)
    result = calibrate_kinematic_weight(fit, encoder, ROOT / "data" / "fractions" / "train_100pct.csv")
    assert len(result["records"]) == 3
    assert 0.01 <= result["kinematic_weight"] <= 100.0


def test_locked_manifest_rejects_change() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "manifest.json"; locked_json(path, {"a": 1}); locked_json(path, {"a": 1})
        try: locked_json(path, {"a": 2})
        except RuntimeError as exc: assert "Locked manifest mismatch" in str(exc)
        else: raise AssertionError("changed manifest was accepted")


def test_primary_analysis_averages_seeds_within_flight() -> None:
    runs = []
    for method, offset in (("nn", 0.0), ("kcnn", -0.1)):
        for seed in FINAL_SEEDS:
            runs.append({"config": {"method": method, "fraction": "005", "seed": seed},
                         "metrics_per_flight": [{"flight_id": f"f{i}", "h_rmse_m": 1.0 + offset,
                                                 "v_rmse_m_s": 1.0 + offset} for i in range(6)]})
    result = primary_analysis(runs, (1.0, 1.0), bootstrap_repeats=100)
    assert np.isclose(result["mean_difference"], -0.1)
    assert result["flights_favoring_kcnn"] == 6


def test_predeclared_unique_training_budget_is_98() -> None:
    assert 2 * len(GRID) * len(SCREEN_SEEDS) + 2 * 5 * len(FINAL_SEEDS) == 98


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test(); print(f"PASS {test.__name__}")
    print(json.dumps({"status": "passed", "tests": len(tests)}))
