"""Core implementation for the preregistered RQ1 NN versus KC-NN study."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn

SCHEMA_VERSION = 2
BLOCKS = ("1", "2", "3", "4", "5")
TARGETS = ("altitude_m", "speed_m_s")
FRACTIONS = ("100", "050", "025", "010", "005")
SCREEN_SEEDS = (11, 29, 47)
FINAL_SEEDS = (11, 29, 47, 71, 97)
TEST_FLIGHTS = {"ses_9", "thaicom_8", "intelsat_35e", "spacex_crs_11", "iridium_next_5", "sso_a"}


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def object_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def locked_json(path: Path, value: object) -> None:
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if canonical_json(previous) != canonical_json(value):
            raise RuntimeError(f"Locked manifest mismatch: {path}. Use a new output directory.")
        return
    atomic_json(path, value)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_flights(flights_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[Path]]:
    train, outer, sources = [], [], []
    paths = sorted(flights_dir.glob("*.csv"))
    if not paths:
        raise ValueError(f"No per-flight CSV files found in {flights_dir}")
    for path in paths:
        rows = read_rows(path)
        if len(rows) != 121:
            raise ValueError(f"{path.name}: expected 121 rows, got {len(rows)}")
        partitions, flight_ids = {r["partition"] for r in rows}, {r["flight_id"] for r in rows}
        if len(partitions) != 1 or len(flight_ids) != 1:
            raise ValueError(f"{path.name}: mixed flight or partition")
        partition, flight_id = next(iter(partitions)), next(iter(flight_ids))
        if partition == "test" or flight_id in TEST_FLIGHTS:
            raise RuntimeError(f"Test trajectory input refused: {path.name}")
        if partition == "train":
            train.extend(rows)
        elif partition == "validation":
            outer.extend(rows)
        else:
            raise ValueError(f"{path.name}: unexpected partition {partition!r}")
        sources.append(path)
    if len(train) != 3388 or len(outer) != 726:
        raise ValueError(f"Expected 3388 train and 726 outer rows; got {len(train)} and {len(outer)}")
    return train, outer, sources


def split_inner(train, outer, split_path: Path):
    split = json.loads(split_path.read_text(encoding="utf-8"))
    fit_ids, inner_ids, outer_ids = map(set, (split["fit"], split["inner_validation"], split["outer_validation"]))
    train_ids, actual_outer = {r["flight_id"] for r in train}, {r["flight_id"] for r in outer}
    if fit_ids & inner_ids or fit_ids | inner_ids != train_ids:
        raise ValueError("Inner split does not partition the 28 train flights")
    if len(fit_ids) != 22 or len(inner_ids) != 6 or outer_ids != actual_outer:
        raise ValueError("Inner/outer split counts or identities do not match")
    return ([r for r in train if r["flight_id"] in fit_ids],
            [r for r in train if r["flight_id"] in inner_ids], split)


@dataclass(frozen=True)
class Encoder:
    payload_median: float
    payload_std: float
    target_mean: tuple[float, float]
    target_scale: tuple[float, float]

    @classmethod
    def fit(cls, rows):
        payload = np.array([float(r["payload_kg"]) if r["payload_kg"] else np.nan for r in rows])
        y = targets(rows)
        median, payload_std, scale = float(np.nanmedian(payload)), float(np.nanstd(payload)), y.std(axis=0)
        if payload_std <= 0 or np.any(scale <= 0):
            raise ValueError("Non-positive training scale")
        return cls(median, payload_std, tuple(y.mean(axis=0)), tuple(scale))

    @property
    def feature_names(self):
        return ("time_normalized", "payload_standardized", "payload_missing") + tuple(f"block_{b}" for b in BLOCKS)

    def transform(self, rows):
        x = np.zeros((len(rows), len(self.feature_names)), dtype=np.float64)
        for i, row in enumerate(rows):
            x[i, 0] = float(row["time_normalized"])
            missing = not bool(row["payload_kg"])
            payload = self.payload_median if missing else float(row["payload_kg"])
            x[i, 1], x[i, 2] = (payload - self.payload_median) / self.payload_std, float(missing)
            block = str(row["block"])
            if block not in BLOCKS:
                raise ValueError(f"Unknown block: {block}")
            x[i, 3 + BLOCKS.index(block)] = 1.0
        return x

    def standardize_targets(self, y):
        return (y - np.asarray(self.target_mean)) / np.asarray(self.target_scale)

    def inverse_targets(self, y):
        return y * np.asarray(self.target_scale) + np.asarray(self.target_mean)

    def as_dict(self):
        return {"payload_median": self.payload_median, "payload_std": self.payload_std,
                "target_mean": list(self.target_mean), "target_scale": list(self.target_scale),
                "feature_names": list(self.feature_names)}


def targets(rows):
    return np.array([[float(r[n]) for n in TARGETS] for r in rows], dtype=np.float64)


def observed_rows(rows, manifest: Path):
    keys = {(r["flight_id"], float(r["time_s"])) for r in read_rows(manifest)}
    row_ids = {r["flight_id"] for r in rows}
    selected = [r for r in rows if (r["flight_id"], float(r["time_s"])) in keys]
    expected = sum(flight_id in row_ids for flight_id, _ in keys)
    if len(selected) != expected:
        raise ValueError(f"Manifest mismatch: {manifest}")
    return selected


class TrajectoryNet(nn.Module):
    def __init__(self, n_inputs=8):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(n_inputs, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 2))
    def forward(self, x):
        return self.layers(x)


def deterministic_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True); torch.set_num_threads(1)


def make_model(seed, n_inputs=8):
    deterministic_seed(seed)
    return TrajectoryNet(n_inputs).double()


def kinematic_loss(model, collocation_x, target_mean, target_scale):
    x = collocation_x.detach().clone().requires_grad_(True)
    pred_std = model(x)
    h = target_mean[0] + target_scale[0] * pred_std[:, 0]
    speed = target_mean[1] + target_scale[1] * pred_std[:, 1]
    vertical_rate = torch.autograd.grad(h.sum(), x, create_graph=True)[0][:, 0] / 120.0
    scale = target_scale[1]
    low, high, neg_speed = torch.relu(-vertical_rate / scale), torch.relu((vertical_rate-speed)/scale), torch.relu(-speed/scale)
    return (low.square()+high.square()+neg_speed.square()).mean(), {
        "vertical_rate": vertical_rate, "speed": speed,
        "violation": (low > 0) | (high > 0) | (neg_speed > 0)}


def objective(model, x_obs, y_obs, x_col, encoder, kinematic_weight):
    data_loss = torch.mean((model(x_obs)-y_obs)**2)
    kin_loss = torch.zeros((), dtype=data_loss.dtype)
    if kinematic_weight:
        kin_loss, _ = kinematic_loss(model, x_col, encoder.target_mean, encoder.target_scale)
    return data_loss + kinematic_weight*kin_loss, data_loss, kin_loss


def gradient_norm(loss, model, retain_graph):
    gradients = torch.autograd.grad(loss, tuple(model.parameters()), retain_graph=retain_graph)
    return float(torch.sqrt(sum(torch.sum(g.square()) for g in gradients)).detach())


def calibrate_kinematic_weight(fit_rows, encoder, manifest: Path, seeds=SCREEN_SEEDS):
    observed = observed_rows(fit_rows, manifest)
    x_obs = torch.tensor(encoder.transform(observed), dtype=torch.float64)
    y_obs = torch.tensor(encoder.standardize_targets(targets(observed)), dtype=torch.float64)
    x_col = torch.tensor(encoder.transform(fit_rows), dtype=torch.float64)
    records, ratios = [], []
    for seed in seeds:
        model = make_model(seed)
        _, data_loss, _ = objective(model, x_obs, y_obs, x_col, encoder, 0.0)
        kin_loss, _ = kinematic_loss(model, x_col, encoder.target_mean, encoder.target_scale)
        gd, gk = gradient_norm(data_loss, model, True), gradient_norm(kin_loss, model, False)
        ratio = gk/gd if gd > 0 else math.nan
        if math.isfinite(ratio) and ratio > 0: ratios.append(ratio)
        records.append({"seed": seed, "data_loss": float(data_loss.detach()), "kinematic_loss": float(kin_loss.detach()),
                        "data_gradient_norm": gd, "kinematic_gradient_norm": gk, "gradient_ratio": ratio})
    median = float(np.median(ratios)) if ratios else math.nan
    fallback = not math.isfinite(median) or median <= 0
    weight = 1.0 if fallback else float(np.clip(1.0/median, 0.01, 100.0))
    return {"rule": "clip(1/median gradient ratio,0.01,100); fallback 1", "seeds": list(seeds),
            "records": records, "median_gradient_ratio": median, "kinematic_weight": weight, "fallback_used": fallback}


def flight_metrics(rows, truth, prediction):
    result, ids = [], np.array([r["flight_id"] for r in rows])
    for flight_id in sorted(set(ids)):
        idx = np.flatnonzero(ids == flight_id); error = prediction[idx]-truth[idx]
        rmse, mae = np.sqrt(np.mean(error**2, axis=0)), np.mean(np.abs(error), axis=0)
        result.append({"flight_id": flight_id, "mission": rows[int(idx[0])]["mission"],
                       "h_rmse_m": float(rmse[0]), "v_rmse_m_s": float(rmse[1]),
                       "h_mae_m": float(mae[0]), "v_mae_m_s": float(mae[1])})
    return result


def selection_score(per_flight, target_scale):
    return float(np.mean([.5*(float(r["h_rmse_m"])/target_scale[0] + float(r["v_rmse_m_s"])/target_scale[1]) for r in per_flight]))


@dataclass(frozen=True)
class TrainConfig:
    method: str
    phase: str
    fraction: str
    seed: int
    learning_rate: float
    weight_decay: float
    max_epochs: int
    checkpoint_interval: int = 10
    stale_checks: int = 25
    def __post_init__(self):
        if self.method not in {"nn", "kcnn"} or self.phase not in {"screen", "final", "smoke"} or self.fraction not in FRACTIONS:
            raise ValueError((self.method, self.phase, self.fraction))
    @property
    def run_id(self):
        return f"{self.phase}_{self.method}_f{self.fraction}_seed{self.seed}_lr{self.learning_rate:g}_wd{self.weight_decay:g}_e{self.max_epochs}"


def initialization_hash(model):
    return hashlib.sha256(b"".join(v.detach().cpu().numpy().tobytes() for v in model.state_dict().values())).hexdigest()


def load_npz_model(path: Path, seed=0, n_inputs=8):
    model = make_model(seed, n_inputs)
    with np.load(path, allow_pickle=False) as saved:
        state = {name: torch.tensor(saved[name], dtype=torch.float64) for name in saved.files}
    model.load_state_dict(state, strict=True); model.eval()
    return model


def validate_resume(output_dir, config, run_fingerprint):
    path = output_dir/"result.json"
    if not path.exists(): return None
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("run_fingerprint") != run_fingerprint or result.get("config") != asdict(config):
        raise RuntimeError(f"Stale or conflicting completed run: {output_dir}")
    weights = output_dir/"weights.npz"
    if not weights.exists() or result.get("weights_sha256") != sha256(weights):
        raise RuntimeError(f"Completed run has missing or changed weights: {output_dir}")
    return result


def write_predictions(path, rows, truth, prediction):
    fields = ["flight_id","mission","time_s","h_true_m","h_pred_m","v_true_m_s","v_pred_m_s"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for row, true, pred in zip(rows, truth, prediction):
            writer.writerow({"flight_id":row["flight_id"],"mission":row["mission"],"time_s":row["time_s"],
                             "h_true_m":true[0],"h_pred_m":pred[0],"v_true_m_s":true[1],"v_pred_m_s":pred[1]})


def train_one(config, fit_rows, evaluation_rows, encoder, manifest, output_dir, run_fingerprint,
              kinematic_weight, checkpoint_rows=None):
    output_dir.mkdir(parents=True, exist_ok=True)
    resumed = validate_resume(output_dir, config, run_fingerprint)
    if resumed is not None: return resumed
    observed = observed_rows(fit_rows, manifest)
    x_obs = torch.tensor(encoder.transform(observed), dtype=torch.float64)
    y_obs = torch.tensor(encoder.standardize_targets(targets(observed)), dtype=torch.float64)
    x_col = torch.tensor(encoder.transform(fit_rows), dtype=torch.float64)
    x_eval, y_eval = torch.tensor(encoder.transform(evaluation_rows), dtype=torch.float64), targets(evaluation_rows)
    x_check = torch.tensor(encoder.transform(checkpoint_rows), dtype=torch.float64) if checkpoint_rows else None
    y_check = targets(checkpoint_rows) if checkpoint_rows else None
    model = make_model(config.seed); initial_hash = initialization_hash(model)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    _, initial_data, _ = objective(model, x_obs, y_obs, x_col, encoder, 0.0)
    initial_kin, _ = kinematic_loss(model, x_col, encoder.target_mean, encoder.target_scale)
    gd, gk = gradient_norm(initial_data, model, True), gradient_norm(initial_kin, model, False)
    best_score, best_epoch, best_state, stale, history = math.inf, 0, None, 0, []
    effective = kinematic_weight if config.method == "kcnn" else 0.0
    started = time.perf_counter()
    for epoch in range(1, config.max_epochs+1):
        model.train(); optimizer.zero_grad(set_to_none=True)
        loss, data_loss, kin_loss = objective(model, x_obs, y_obs, x_col, encoder, effective)
        if not torch.isfinite(loss): raise FloatingPointError(f"Non-finite loss: {config.run_id} epoch {epoch}")
        loss.backward(); optimizer.step()
        if checkpoint_rows is None:
            if epoch == config.max_epochs:
                best_epoch, best_state = epoch, copy.deepcopy(model.state_dict())
                history.append({"epoch":epoch,"loss":float(loss.detach()),"data_loss":float(data_loss.detach()),"kinematic_loss":float(kin_loss.detach())})
            continue
        if epoch % config.checkpoint_interval and epoch != config.max_epochs: continue
        model.eval()
        with torch.no_grad(): pred = encoder.inverse_targets(model(x_check).numpy())
        score = selection_score(flight_metrics(checkpoint_rows, y_check, pred), encoder.target_scale)
        history.append({"epoch":epoch,"loss":float(loss.detach()),"data_loss":float(data_loss.detach()),"kinematic_loss":float(kin_loss.detach()),"checkpoint_score":score})
        if score < best_score-1e-8:
            best_score, best_epoch, best_state, stale = score, epoch, copy.deepcopy(model.state_dict()), 0
        else: stale += 1
        if stale >= config.stale_checks: break
    if best_state is None: raise RuntimeError("No state selected")
    training_seconds = time.perf_counter() - started
    model.load_state_dict(best_state); model.eval()
    with torch.no_grad(): eval_pred = encoder.inverse_targets(model(x_eval).numpy())
    metrics = flight_metrics(evaluation_rows, y_eval, eval_pred)
    kin_eval, diag = kinematic_loss(model, x_eval, encoder.target_mean, encoder.target_scale)
    weights = output_dir/"weights.npz"
    np.savez_compressed(weights, **{k:v.detach().numpy() for k,v in best_state.items()})
    write_predictions(output_dir/"evaluation_predictions.csv", evaluation_rows, y_eval, eval_pred)
    atomic_json(output_dir/"history.json", history)
    result = {"schema_version":SCHEMA_VERSION,"config":asdict(config),"run_id":config.run_id,
              "run_fingerprint":run_fingerprint,"weights_sha256":sha256(weights),
              "n_observed_rows":len(observed),"n_collocation_rows":len(fit_rows),
              "n_checkpoint_rows":len(checkpoint_rows) if checkpoint_rows else 0,"n_evaluation_rows":len(evaluation_rows),
              "test_trajectory_files_in_inputs":0,"best_epoch":best_epoch,"last_epoch":epoch,
              "training_seconds":training_seconds,
              "checkpoint_score":None if checkpoint_rows is None else best_score,
              "evaluation_score":selection_score(metrics, encoder.target_scale),
              "h_rmse_m":float(np.mean([m["h_rmse_m"] for m in metrics])),
              "v_rmse_m_s":float(np.mean([m["v_rmse_m_s"] for m in metrics])),
              "kinematic_weight":effective,"initial_data_loss":float(initial_data.detach()),
              "initial_kinematic_loss":float(initial_kin.detach()),"initial_data_gradient_norm":gd,
              "initial_kinematic_gradient_norm":gk,"kinematic_loss_evaluation":float(kin_eval.detach()),
              "kinematic_violation_fraction_evaluation":float(diag["violation"].double().mean().detach()),
              "metrics_per_flight":metrics,"initialization_sha256":initial_hash}
    atomic_json(output_dir/"result.json", result)
    return result


def input_manifest(paths: Iterable[Path]):
    return [{"path":str(p),"size":p.stat().st_size,"sha256":sha256(p)} for p in sorted(paths)]
