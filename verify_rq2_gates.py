#!/usr/bin/env python3
"""Verify both the blocking and success paths of the identity-gated splitter."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    root = Path(__file__).resolve().parent
    review = root / "outputs/flightsketch_audit/identity_review_template.csv"
    splitter = root / "prepare_rq2_split.py"

    with tempfile.TemporaryDirectory(prefix="rq2_gate_test_") as temp_name:
        temp = Path(temp_name)
        blocked_output = temp / "blocked.csv"
        blocked = subprocess.run(
            [sys.executable, str(splitter), "--identity-review", str(review), "--output", str(blocked_output)],
            check=False, capture_output=True, text=True,
        )
        blocked_ok = blocked.returncode == 2 and not blocked_output.exists()

        rows = read_csv(review)
        for row in rows:
            row["identity_decision"] = "confirmed_configuration_group"
            row["canonical_vehicle_id"] = "synthetic-" + hashlib.sha256(row["vehicle_key"].encode()).hexdigest()[:16]
            row["configuration_policy"] = "configuration_specific"
            row["evidence_source"] = "synthetic_verification_fixture"
        resolved = temp / "resolved_fixture.csv"
        with resolved.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        split_output = temp / "split.csv"
        completed = subprocess.run(
            [sys.executable, str(splitter), "--identity-review", str(resolved), "--output", str(split_output)],
            check=False, capture_output=True, text=True,
        )
        split_rows = read_csv(split_output) if split_output.exists() else []
        counts = Counter(row["split"] for row in split_rows)
        completed_ok = (
            completed.returncode == 0
            and len(split_rows) == 68
            and counts["external_contributor_sensitivity_sealed"] == 4
            and counts["test_sealed"] >= 3
            and counts["validation"] >= 3
            and all(row["split_seed"] == "rq2-flightsketch-v1-identity-gated" for row in split_rows)
        )

    result = {
        "status": "passed" if blocked_ok and completed_ok else "failed",
        "checks": {
            "pending_review_blocks_split": blocked_ok,
            "blocked_path_writes_no_manifest": blocked_ok,
            "resolved_fixture_completes": completed_ok,
            "external_groups_are_sealed": counts["external_contributor_sensitivity_sealed"] == 4,
            "validation_minimum_respected": counts["validation"] >= 3,
            "test_minimum_respected": counts["test_sealed"] >= 3,
            "fixed_seed_recorded": bool(split_rows) and all(
                row["split_seed"] == "rq2-flightsketch-v1-identity-gated" for row in split_rows
            ),
        },
        "synthetic_split_counts": dict(counts),
        "production_split_rows_written": 0,
        "model_training_runs": 0,
        "rq1_test_trajectory_inputs": 0,
    }
    output = root / "outputs/flightsketch_audit/rq2_gate_verification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

