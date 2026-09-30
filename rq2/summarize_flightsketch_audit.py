#!/usr/bin/env python3
"""Create shareable, license-safe summaries from the FlightSketch audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def truth(value: object) -> bool:
    return str(value).strip().lower() == "true"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def family_name(name: str) -> str:
    value = re.sub(r"\s+", " ", name.lower()).strip()
    return re.sub(r"\s*\(\s*(\d+)\s*\)\s*", r" (\1)", value)


def broader_family_name(name: str) -> str:
    value = re.sub(r"\s*\(\d+\)\s*", " ", family_name(name))
    return re.sub(r"\s+", " ", value).strip()


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    n = len(ordered)

    def at(p: float) -> float:
        return ordered[round((n - 1) * p)]

    return {
        "min": ordered[0],
        "q25": at(0.25),
        "median": statistics.median(ordered),
        "q75": at(0.75),
        "max": ordered[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/flightsketch_audit"))
    args = parser.parse_args()
    root = args.output_dir

    with (root / "flight_audit.csv").open(newline="", encoding="utf-8") as handle:
        flights = list(csv.DictReader(handle))
    with (root / "vehicle_groups.csv").open(newline="", encoding="utf-8") as handle:
        groups = list(csv.DictReader(handle))

    passing = [row for row in flights if truth(row["quality_pass"])]
    manifest_fields = [
        "flight_id", "vehicle_key", "uploader", "vehicle_name_normalized",
        "source_page_url", "row_count", "has_acceleration", "median_dt_s",
        "duration_s", "altitude_span_ft", "max_positive_velocity_ft_s", "raw_sha256",
    ]
    manifest = [{key: row.get(key, "") for key in manifest_fields} for row in passing]
    manifest_path = root / "rq2_candidate_manifest.csv"
    write_csv(manifest_path, manifest)

    broad_members: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in groups:
        broad_members[(row["uploader"].lower(), broader_family_name(row["vehicle_name_normalized"]))].add(
            row["vehicle_name_normalized"]
        )

    review_rows: list[dict[str, object]] = []
    for row in groups:
        name = row["vehicle_name_normalized"]
        generic = bool(
            re.fullmatch(r"test flight|flight|rocket|unknown", name)
            or re.match(r"^20\d\d[-_/]\d\d[-_/]\d\d", name)
        )
        variants = sorted(broad_members[(row["uploader"].lower(), broader_family_name(name))])
        collision = len(variants) > 1
        flags = ["identity_confirmation_required"]
        if generic:
            flags.append("nonidentifying_label")
        if collision:
            flags.append("possible_variant_family_collision")
        review_rows.append({
            **row,
            "broader_name_family": broader_family_name(name),
            "related_normalized_labels": " | ".join(variants),
            "review_flags": "|".join(flags),
            "provisional_modeling_status": "hold_for_manual_confirmation" if generic else "pilot_candidate_only",
        })
    review_path = root / "group_review_flags.csv"
    write_csv(review_path, review_rows)

    contributors = Counter(row["uploader"] for row in passing)
    metric_fields = [
        "row_count", "median_dt_s", "duration_s", "altitude_span_ft",
        "max_positive_velocity_ft_s",
    ]
    stats = {
        "status": "pilot_feasible_with_major_sampling_limitations",
        "passing_flights": len(passing),
        "automatic_vehicle_groups": sum(truth(row["eligible_for_rq2"]) for row in groups),
        "contributors": len(contributors),
        "contributor_flight_counts": dict(contributors.most_common()),
        "largest_contributor_share": contributors.most_common(1)[0][1] / len(passing),
        "top_five_contributor_share": sum(v for _, v in contributors.most_common(5)) / len(passing),
        "groups_with_nonidentifying_labels": sum("nonidentifying_label" in row["review_flags"] for row in review_rows),
        "groups_with_possible_variant_collision": sum(
            "possible_variant_family_collision" in row["review_flags"] for row in review_rows
        ),
        "metric_distributions": {
            field: quantiles([float(row[field]) for row in passing]) for field in metric_fields
        },
        "scientific_scope": (
            "Suitable for a pilot vehicle-grouped study after manual identity confirmation; "
            "not sufficient by itself for a strong contributor-generalization claim."
        ),
        "raw_redistribution": "prohibited_pending_explicit_permission_or_license",
        "model_training_runs": 0,
        "rq1_test_trajectory_inputs": 0,
    }
    stats_path = root / "audit_statistics.json"
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")

    manifest_json = {
        path.name: {"sha256": sha256(path), "size_bytes": path.stat().st_size}
        for path in (manifest_path, review_path, stats_path)
    }
    derived_path = root / "derived_artifacts_manifest.json"
    derived_path.write_text(json.dumps(manifest_json, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
