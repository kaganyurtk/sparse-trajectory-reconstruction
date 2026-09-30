#!/usr/bin/env python3
"""Independently verify generated FlightSketch curation artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/flightsketch_audit"))
    args = parser.parse_args()
    root: Path = args.output_dir
    summary_path = root / "curation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    derived_manifest_path = root / "derived_artifacts_manifest.json"
    derived_manifest = (
        json.loads(derived_manifest_path.read_text(encoding="utf-8"))
        if derived_manifest_path.exists()
        else {}
    )
    source = read_csv(root / "source_index.csv")
    selected = read_csv(root / "candidate_selection.csv")
    audit = read_csv(root / "flight_audit.csv")
    groups = read_csv(root / "vehicle_groups.csv")

    ids = [int(row["flight_id"]) for row in source]
    selected_ids = [int(row["flight_id"]) for row in selected]
    audit_ids = [int(row["flight_id"]) for row in audit]
    selected_counts = Counter(row["vehicle_key"] for row in selected)
    passing_counts = Counter(row["vehicle_key"] for row in audit if truth(row["quality_pass"]))
    group_map = {row["vehicle_key"]: row for row in groups}

    checks = {
        "summary_complete": summary["status"] == "complete",
        "source_ids_unique": len(ids) == len(set(ids)),
        "selected_ids_unique": len(selected_ids) == len(set(selected_ids)),
        "audit_matches_selection": sorted(audit_ids) == sorted(selected_ids),
        "no_obvious_nonflight_selected": all(not truth(row["obvious_nonflight"]) for row in selected),
        "candidate_group_minimum_respected": all(
            int(group_map[key]["indexed_record_count"])
            >= summary["thresholds"]["min_indexed_records_per_group"]
            for key in selected_counts
        ),
        "candidate_group_cap_respected": all(
            count <= summary["thresholds"]["max_selected_records_per_group"]
            for count in selected_counts.values()
        ),
        "group_pass_counts_recompute": all(
            int(row["passing_record_count"]) == passing_counts[row["vehicle_key"]]
            for row in groups
        ),
        "group_eligibility_recompute": all(
            truth(row["eligible_for_rq2"])
            == (
                passing_counts[row["vehicle_key"]]
                >= summary["thresholds"]["min_passing_records_per_eligible_group"]
            )
            for row in groups
        ),
        "counts_recompute": (
            summary["counts"]["indexed_records"] == len(source)
            and summary["counts"]["candidate_records"] == len(selected)
            and summary["counts"]["audited_records"] == len(audit)
            and summary["counts"]["candidate_groups"] == len(groups)
            and summary["counts"]["quality_pass_records"]
            == sum(truth(row["quality_pass"]) for row in audit)
            and summary["counts"]["eligible_groups"]
            == sum(truth(row["eligible_for_rq2"]) for row in groups)
        ),
        "artifact_hashes": all(
            sha256(root / name) == metadata["sha256"]
            for name, metadata in summary["artifacts"].items()
        ),
        "derived_artifact_hashes": all(
            sha256(root / name) == metadata["sha256"]
            for name, metadata in derived_manifest.items()
        ),
        "raw_files_not_manifested_for_sharing": all(
            not name.startswith("raw_private/")
            and not (name.startswith("flight_") and name.endswith(".csv") and name != "flight_audit.csv")
            for name in summary["artifacts"]
        ),
        "test_inputs_zero": summary["test_trajectory_inputs"] == 0,
        "model_training_zero": summary["model_training_runs"] == 0,
    }
    verification = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "verified_counts": {
            "source_rows": len(source),
            "selected_rows": len(selected),
            "audit_rows": len(audit),
            "group_rows": len(groups),
        },
    }
    output = root / "verification.json"
    output.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(verification, indent=2))
    if verification["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
