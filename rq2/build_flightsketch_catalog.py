#!/usr/bin/env python3
"""Build a results-blind, group-balanced FlightSketch feasibility catalog."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import random
import re
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

INDEX_URL = "https://flightsketch.com/flight-filter/"
FLIGHT_URL = "https://flightsketch.com/flights/{flight_id}/"
USER_AGENT = "RQ2-academic-feasibility-audit/1.0 (public-data quality check)"
REQUIRED = ("time", "altitude", "velocity")
OBVIOUS_NONFLIGHT = re.compile(
    r"\b(chamber|vacuum|checkout|bench|ground[ -]?test)\b", re.IGNORECASE
)

THRESHOLDS = {
    "min_rows": 250,
    "min_finite_fraction": 0.99,
    "min_increasing_time_fraction": 0.995,
    "median_dt_s": [0.015, 0.25],
    "duration_s": [8.0, 300.0],
    "altitude_span_ft": [50.0, 100000.0],
    "max_positive_velocity_ft_s": [30.0, 5000.0],
    "min_indexed_records_per_group": 5,
    "max_selected_records_per_group": 12,
    "min_passing_records_per_eligible_group": 3,
}


@dataclass(frozen=True)
class IndexRow:
    flight_id: int
    title: str
    description: str
    uploader: str
    vehicle_name_normalized: str
    vehicle_key: str
    source_page_url: str
    obvious_nonflight: bool


def fetch(url: str, attempts: int = 4, timeout: int = 45) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.0 * (2**attempt))
    assert last is not None
    raise last


def clean_html(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<.*?>", "", value))).strip()


def normalize_vehicle_name(title: str) -> str:
    value = html.unescape(title).lower().replace("’", "'")
    value = re.sub(r"\b(?:flight|flt|launch|run)\s*#?\s*\d+\b", " ", value)
    value = re.sub(r"\bflight\s+[ivxlcdm]+\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -_.,")
    return value


def parse_index(raw: str) -> list[IndexRow]:
    pattern = re.compile(
        r'<a href="(\d+)"[^>]*>.*?<h3>(.*?)</h3>.*?<h5>(.*?)</h5>'
        r".*?Posted by:\s*([^<]+)",
        re.DOTALL,
    )
    rows: list[IndexRow] = []
    for flight_id_raw, title_raw, description_raw, uploader_raw in pattern.findall(raw):
        title = clean_html(title_raw)
        description = clean_html(description_raw)
        uploader = clean_html(uploader_raw)
        normalized = normalize_vehicle_name(title)
        vehicle_key = f"{uploader.casefold()}::{normalized}" if normalized else ""
        rows.append(
            IndexRow(
                flight_id=int(flight_id_raw),
                title=title,
                description=description,
                uploader=uploader,
                vehicle_name_normalized=normalized,
                vehicle_key=vehicle_key,
                source_page_url=FLIGHT_URL.format(flight_id=flight_id_raw),
                obvious_nonflight=bool(OBVIOUS_NONFLIGHT.search(f"{title} {description}")),
            )
        )
    if not rows:
        raise RuntimeError("No FlightSketch index rows parsed")
    return sorted(rows, key=lambda row: row.flight_id)


def stable_order(row: IndexRow) -> str:
    payload = f"20260921|{row.vehicle_key}|{row.flight_id}".encode()
    return hashlib.sha256(payload).hexdigest()


def select_candidates(rows: list[IndexRow]) -> tuple[list[IndexRow], Counter[str]]:
    groups: dict[str, list[IndexRow]] = defaultdict(list)
    for row in rows:
        if row.vehicle_key and not row.obvious_nonflight:
            groups[row.vehicle_key].append(row)
    counts = Counter({key: len(values) for key, values in groups.items()})
    chosen: list[IndexRow] = []
    for key in sorted(groups):
        values = groups[key]
        if len(values) < THRESHOLDS["min_indexed_records_per_group"]:
            continue
        ordered = sorted(values, key=stable_order)
        chosen.extend(ordered[: THRESHOLDS["max_selected_records_per_group"]])
    return sorted(chosen, key=lambda row: row.flight_id), counts


def extract_csv_url(page_text: str) -> str | None:
    match = re.search(
        r'href="(https://storage\.googleapis\.com/flightsketch-prod/[^"]+\.csv)"',
        page_text,
    )
    return html.unescape(match.group(1)) if match else None


def finite_float(value: str | None) -> float | None:
    try:
        number = float(value) if value is not None else math.nan
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def median_initial_altitude(times: list[float], altitudes: list[float]) -> float:
    start = min(times)
    values = [a for t, a in zip(times, altitudes) if t <= start + 2.0]
    return statistics.median(values or altitudes[: min(20, len(altitudes))])


def audit_csv(raw: bytes) -> dict[str, object]:
    text = raw.decode("utf-8-sig", "replace")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = tuple(reader.fieldnames or ())
    records = list(reader)
    result: dict[str, object] = {
        "csv_columns": "|".join(fieldnames),
        "row_count": len(records),
        "has_acceleration": all(x in fieldnames for x in ("acc_x", "acc_y", "acc_z")),
    }
    failures: list[str] = []
    missing = [name for name in REQUIRED if name not in fieldnames]
    if missing:
        failures.append("missing_columns:" + ",".join(missing))
        result.update({"quality_pass": False, "failure_reasons": "|".join(failures)})
        return result

    parsed = [[finite_float(record.get(name)) for name in REQUIRED] for record in records]
    total_cells = max(1, len(parsed) * len(REQUIRED))
    finite_cells = sum(value is not None for row in parsed for value in row)
    finite_fraction = finite_cells / total_cells
    complete = [row for row in parsed if all(value is not None for value in row)]
    result["finite_fraction"] = finite_fraction
    if len(records) < THRESHOLDS["min_rows"]:
        failures.append("too_few_rows")
    if finite_fraction < THRESHOLDS["min_finite_fraction"]:
        failures.append("insufficient_finite_values")
    if len(complete) < 3:
        failures.append("too_few_complete_rows")
        result.update({"quality_pass": False, "failure_reasons": "|".join(failures)})
        return result

    times = [row[0] for row in complete]
    altitudes = [row[1] for row in complete]
    velocities = [row[2] for row in complete]
    assert all(value is not None for value in times + altitudes + velocities)
    times_f = [float(value) for value in times]
    alt_f = [float(value) for value in altitudes]
    vel_f = [float(value) for value in velocities]
    deltas = [b - a for a, b in zip(times_f, times_f[1:])]
    increasing_fraction = sum(delta > 0 for delta in deltas) / max(1, len(deltas))
    positive_deltas = [delta for delta in deltas if delta > 0]
    median_dt = statistics.median(positive_deltas) if positive_deltas else math.nan
    duration = max(times_f) - min(times_f)
    altitude_min = min(alt_f)
    altitude_max = max(alt_f)
    altitude_span = altitude_max - altitude_min
    max_positive_velocity = max(vel_f)
    baseline = median_initial_altitude(times_f, alt_f)
    launch_index = next(
        (
            index
            for index, (altitude, velocity) in enumerate(zip(alt_f, vel_f))
            if altitude > baseline + 5.0 or velocity > 10.0
        ),
        None,
    )
    apogee_index = max(range(len(alt_f)), key=alt_f.__getitem__)
    apogee_after_launch = launch_index is not None and apogee_index > launch_index

    result.update(
        {
            "complete_row_count": len(complete),
            "increasing_time_fraction": increasing_fraction,
            "median_dt_s": median_dt,
            "duration_s": duration,
            "altitude_min_ft": altitude_min,
            "altitude_max_ft": altitude_max,
            "altitude_span_ft": altitude_span,
            "max_positive_velocity_ft_s": max_positive_velocity,
            "launch_time_s": times_f[launch_index] if launch_index is not None else None,
            "apogee_time_s": times_f[apogee_index],
            "apogee_after_launch": apogee_after_launch,
        }
    )
    if increasing_fraction < THRESHOLDS["min_increasing_time_fraction"]:
        failures.append("nonmonotonic_time")
    if not (THRESHOLDS["median_dt_s"][0] <= median_dt <= THRESHOLDS["median_dt_s"][1]):
        failures.append("sample_interval_out_of_range")
    if not (THRESHOLDS["duration_s"][0] <= duration <= THRESHOLDS["duration_s"][1]):
        failures.append("duration_out_of_range")
    if not (
        THRESHOLDS["altitude_span_ft"][0]
        <= altitude_span
        <= THRESHOLDS["altitude_span_ft"][1]
    ):
        failures.append("altitude_span_out_of_range")
    if not (
        THRESHOLDS["max_positive_velocity_ft_s"][0]
        <= max_positive_velocity
        <= THRESHOLDS["max_positive_velocity_ft_s"][1]
    ):
        failures.append("velocity_out_of_range")
    if not apogee_after_launch:
        failures.append("no_valid_launch_to_apogee_sequence")
    result["quality_pass"] = not failures
    result["failure_reasons"] = "|".join(failures)
    return result


def inspect_flight(row: IndexRow, raw_dir: Path) -> dict[str, object]:
    base = asdict(row)
    raw_path = raw_dir / f"flight_{row.flight_id}.csv"
    try:
        # Safe restart support: a completed raw download is immutable input for the
        # audit. Reuse it instead of re-requesting the public page and CSV.
        if raw_path.exists() and raw_path.stat().st_size > 0:
            csv_raw = raw_path.read_bytes()
            audit = audit_csv(csv_raw)
            return {
                **base,
                "download_status": "ok_cached",
                "csv_source_url": "",
                "raw_sha256": hashlib.sha256(csv_raw).hexdigest(),
                "raw_size_bytes": len(csv_raw),
                **audit,
            }
        page_raw = fetch(row.source_page_url)
        csv_url = extract_csv_url(page_raw.decode("utf-8", "replace"))
        if not csv_url:
            return {**base, "download_status": "no_csv_link", "quality_pass": False,
                    "failure_reasons": "no_csv_link"}
        csv_raw = fetch(csv_url)
        raw_path.write_bytes(csv_raw)
        audit = audit_csv(csv_raw)
        return {
            **base,
            "download_status": "ok",
            "csv_source_url": csv_url,
            "raw_sha256": hashlib.sha256(csv_raw).hexdigest(),
            "raw_size_bytes": len(csv_raw),
            **audit,
        }
    except Exception as exc:  # preserve a per-flight failure rather than aborting the audit
        return {
            **base,
            "download_status": "error",
            "quality_pass": False,
            "failure_reasons": f"download_error:{type(exc).__name__}",
        }


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    materialized = list(rows)
    fieldnames: list[str] = []
    for row in materialized:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(materialized)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/flightsketch_audit"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--index-only", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Deterministic smoke-test limit")
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw_private"
    raw_dir.mkdir(exist_ok=True)

    index_bytes = fetch(INDEX_URL)
    index_rows = parse_index(index_bytes.decode("utf-8", "replace"))
    source_index_path = output_dir / "source_index.csv"
    write_csv(source_index_path, (asdict(row) for row in index_rows))
    candidates, indexed_group_counts = select_candidates(index_rows)
    if args.limit is not None:
        candidates = candidates[: args.limit]
    selection_path = output_dir / "candidate_selection.csv"
    write_csv(selection_path, (asdict(row) for row in candidates))

    if args.index_only:
        print(json.dumps({"indexed": len(index_rows), "selected": len(candidates)}, indent=2))
        return

    results: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(inspect_flight, row, raw_dir): row for row in candidates}
        for completed, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if completed % 25 == 0 or completed == len(futures):
                print(f"audited {completed}/{len(futures)}", flush=True)
    results.sort(key=lambda row: int(row["flight_id"]))
    audit_path = output_dir / "flight_audit.csv"
    write_csv(audit_path, results)

    by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in results:
        by_group[str(row["vehicle_key"])].append(row)
    group_rows: list[dict[str, object]] = []
    for key, values in sorted(by_group.items()):
        passes = sum(bool(value.get("quality_pass")) for value in values)
        first = values[0]
        group_rows.append(
            {
                "vehicle_key": key,
                "uploader": first["uploader"],
                "vehicle_name_normalized": first["vehicle_name_normalized"],
                "indexed_record_count": indexed_group_counts[key],
                "selected_record_count": len(values),
                "downloaded_record_count": sum(
                    str(value.get("download_status", "")).startswith("ok") for value in values
                ),
                "passing_record_count": passes,
                "eligible_for_rq2": passes >= THRESHOLDS["min_passing_records_per_eligible_group"],
            }
        )
    group_path = output_dir / "vehicle_groups.csv"
    write_csv(group_path, group_rows)

    failure_counts: Counter[str] = Counter()
    for row in results:
        for reason in str(row.get("failure_reasons", "")).split("|"):
            if reason:
                failure_counts[reason] += 1
    summary = {
        "status": "complete",
        "source": {
            "index_url": INDEX_URL,
            "retrieved_unix_time": time.time(),
            "raw_index_sha256": hashlib.sha256(index_bytes).hexdigest(),
            "redistribution_status": "not_explicitly_licensed; raw CSV cache is private",
        },
        "thresholds": THRESHOLDS,
        "counts": {
            "indexed_records": len(index_rows),
            "nonempty_title_records": sum(bool(row.title) for row in index_rows),
            "provisional_groups": len({row.vehicle_key for row in index_rows if row.vehicle_key}),
            "candidate_records": len(candidates),
            "audited_records": len(results),
            "download_ok": sum(
                str(row.get("download_status", "")).startswith("ok") for row in results
            ),
            "quality_pass_records": sum(bool(row.get("quality_pass")) for row in results),
            "candidate_groups": len(group_rows),
            "eligible_groups": sum(bool(row["eligible_for_rq2"]) for row in group_rows),
            "eligible_group_passing_flights": sum(
                int(row["passing_record_count"]) for row in group_rows if row["eligible_for_rq2"]
            ),
        },
        "failure_reason_counts": dict(sorted(failure_counts.items())),
        "artifacts": {
            path.name: {"sha256": file_sha256(path), "size_bytes": path.stat().st_size}
            for path in (source_index_path, selection_path, audit_path, group_path)
        },
        "test_trajectory_inputs": 0,
        "model_training_runs": 0,
    }
    summary_path = output_dir / "curation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
