#!/usr/bin/env python3
"""Create an RQ2 split only after every identity decision is resolved."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ALLOWED_DECISIONS = {"confirmed_same_airframe", "confirmed_configuration_group", "exclude"}
SEED = "rq2-flightsketch-v1-identity-gated"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def stable_key(value: str) -> str:
    return hashlib.sha256(f"{SEED}::{value}".encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/rq2_split_manifest.csv"))
    parser.add_argument("--dominant-uploader", default="bcawley1, Bernard")
    args = parser.parse_args()
    rows = read_csv(args.identity_review)

    invalid = [row for row in rows if row["identity_decision"] not in ALLOWED_DECISIONS]
    missing_id = [
        row for row in rows
        if row["identity_decision"] != "exclude" and not row["canonical_vehicle_id"].strip()
    ]
    if invalid or missing_id:
        status = {
            "status": "blocked",
            "reason": "identity_review_incomplete",
            "invalid_or_pending_decisions": len(invalid),
            "missing_canonical_vehicle_ids": len(missing_id),
            "split_rows_written": 0,
            "model_training_runs": 0,
        }
        print(json.dumps(status, indent=2))
        raise SystemExit(2)

    included = [row for row in rows if row["identity_decision"] != "exclude"]
    by_vehicle: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in included:
        by_vehicle[row["canonical_vehicle_id"].strip()].append(row)
    mixed_uploaders = {
        vehicle: sorted({row["uploader"] for row in members})
        for vehicle, members in by_vehicle.items()
        if len({row["uploader"] for row in members}) > 1
    }
    if mixed_uploaders:
        raise SystemExit(f"canonical IDs cross uploader boundaries: {mixed_uploaders}")

    primary = sorted(
        [vehicle for vehicle, members in by_vehicle.items() if members[0]["uploader"] == args.dominant_uploader],
        key=stable_key,
    )
    external = sorted(
        [vehicle for vehicle, members in by_vehicle.items() if members[0]["uploader"] != args.dominant_uploader],
        key=stable_key,
    )
    if len(primary) < 20:
        raise SystemExit("fewer than 20 confirmed primary-cohort vehicles; split is not defensible")

    n_total = len(primary)
    n_test = max(3, round(n_total * 0.15))
    n_validation = max(3, round(n_total * 0.15))
    assignment: dict[str, str] = {}
    for index, vehicle in enumerate(primary):
        if index < n_test:
            assignment[vehicle] = "test_sealed"
        elif index < n_test + n_validation:
            assignment[vehicle] = "validation"
        else:
            assignment[vehicle] = "train"
    for vehicle in external:
        assignment[vehicle] = "external_contributor_sensitivity_sealed"

    output_rows: list[dict[str, object]] = []
    for vehicle, members in sorted(by_vehicle.items()):
        output_rows.append({
            "canonical_vehicle_id": vehicle,
            "uploader": members[0]["uploader"],
            "split": assignment[vehicle],
            "source_vehicle_keys": " | ".join(sorted(row["vehicle_key"] for row in members)),
            "passing_records": sum(int(row["passing_records"]) for row in members),
            "split_seed": SEED,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(json.dumps({"status": "complete", "split_counts": Counter(assignment.values())}, indent=2))


if __name__ == "__main__":
    main()

