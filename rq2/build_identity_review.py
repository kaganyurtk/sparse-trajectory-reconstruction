#!/usr/bin/env python3
"""Build a metadata-only identity review packet for provisional RQ2 groups."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

MOTOR_RE = re.compile(r"\b(?:[A-O]\d+(?:\.\d+)?(?:-[A-Za-z0-9]+)?)\b", re.I)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def shorten(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, default=Path("outputs/flightsketch_audit"))
    args = parser.parse_args()
    root = args.audit_dir
    flights = read_csv(root / "flight_audit.csv")
    groups = read_csv(root / "group_review_flags.csv")

    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in flights:
        if row["quality_pass"].lower() == "true":
            by_group[row["vehicle_key"]].append(row)

    review_rows: list[dict[str, object]] = []
    for group in groups:
        rows = sorted(by_group[group["vehicle_key"]], key=lambda item: int(item["flight_id"]))
        texts = [f"{row['title']} {row['description']}" for row in rows]
        motors = sorted({token.upper() for text in texts for token in MOTOR_RE.findall(text)})
        title_variants = sorted({row["title"].strip() for row in rows})
        descriptions = []
        for row in rows:
            description = shorten(row["description"])
            if description and description not in descriptions:
                descriptions.append(description)
            if len(descriptions) == 3:
                break
        review_rows.append({
            "vehicle_key": group["vehicle_key"],
            "uploader": group["uploader"],
            "normalized_label": group["vehicle_name_normalized"],
            "indexed_records": int(group["indexed_record_count"]),
            "passing_records": int(group["passing_record_count"]),
            "broader_name_family": group["broader_name_family"],
            "automatic_review_flags": group["review_flags"],
            "related_labels": group["related_normalized_labels"],
            "observed_title_variants": " | ".join(title_variants),
            "observed_motor_tokens": " | ".join(motors),
            "sample_descriptions": " | ".join(descriptions),
            "passing_flight_ids": " | ".join(row["flight_id"] for row in rows),
            "identity_decision": "pending",
            "canonical_vehicle_id": "",
            "configuration_policy": "pending",
            "evidence_source": "",
            "reviewer_notes": "",
        })

    output_path = root / "identity_review_template.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]))
        writer.writeheader()
        writer.writerows(review_rows)
    (root / "identity_review_template.json").write_text(
        json.dumps(review_rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary = {
        "rows": len(review_rows),
        "pending_identity_decisions": sum(row["identity_decision"] == "pending" for row in review_rows),
        "nonidentifying_label_rows": sum("nonidentifying_label" in str(row["automatic_review_flags"]) for row in review_rows),
        "possible_variant_collision_rows": sum("possible_variant_family_collision" in str(row["automatic_review_flags"]) for row in review_rows),
        "model_training_runs": 0,
        "rq1_test_trajectory_inputs": 0,
    }
    (root / "identity_review_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
