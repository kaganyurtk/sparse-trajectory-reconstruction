"""Post-hoc descriptive diagnostics on outer-validation predictions; never tunes a model."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


WINDOWS = ((0, 30), (31, 60), (61, 90), (91, 120))


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "outputs" / "full_v2"
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    records = []
    for result in summary["final_runs"]:
        path = output / result["run_id"] / "evaluation_predictions.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for start, end in WINDOWS:
            window = [r for r in rows if start <= float(r["time_s"]) <= end]
            h_error = np.array([float(r["h_pred_m"]) - float(r["h_true_m"]) for r in window])
            v_error = np.array([float(r["v_pred_m_s"]) - float(r["v_true_m_s"]) for r in window])
            records.append({
                "fraction": result["config"]["fraction"], "method": result["config"]["method"],
                "seed": result["config"]["seed"], "window_s": f"{start}-{end}",
                "h_rmse_m": float(np.sqrt(np.mean(h_error ** 2))),
                "v_rmse_m_s": float(np.sqrt(np.mean(v_error ** 2))),
                "h_bias_m": float(np.mean(h_error)), "v_bias_m_s": float(np.mean(v_error)),
            })
    aggregates = []
    for fraction in ("100", "050", "025", "010", "005"):
        for method in ("nn", "kcnn"):
            for start, end in WINDOWS:
                subset = [r for r in records if r["fraction"] == fraction and r["method"] == method and r["window_s"] == f"{start}-{end}"]
                aggregates.append({"fraction": fraction, "method": method, "window_s": f"{start}-{end}",
                                   **{name: float(np.mean([r[name] for r in subset]))
                                      for name in ("h_rmse_m", "v_rmse_m_s", "h_bias_m", "v_bias_m_s")}})
    result = {"status": "descriptive_only_no_tuning", "windows": [f"{a}-{b}" for a, b in WINDOWS],
              "seed_level_records": records, "aggregates": aggregates}
    (output / "validation_diagnostics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    sparse = [r for r in aggregates if r["fraction"] == "005"]
    lines = ["# Outer-validation zaman-bazlı tanı", "",
             "Bu analiz betimseldir; model veya test planı seçmek için kullanılmamıştır.", "",
             "| Zaman (s) | NN h RMSE (m) | KC-NN h RMSE (m) | NN v RMSE (m/s) | KC-NN v RMSE (m/s) |", "|---|---:|---:|---:|---:|"]
    for window in [f"{a}-{b}" for a, b in WINDOWS]:
        nn = next(r for r in sparse if r["window_s"] == window and r["method"] == "nn")
        kc = next(r for r in sparse if r["window_s"] == window and r["method"] == "kcnn")
        lines.append(f"| {window} | {nn['h_rmse_m']:.2f} | {kc['h_rmse_m']:.2f} | {nn['v_rmse_m_s']:.2f} | {kc['v_rmse_m_s']:.2f} |")
    (root / "VALIDATION_DIAGNOSTICS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "aggregate_rows": len(aggregates)}, indent=2))


if __name__ == "__main__":
    main()
