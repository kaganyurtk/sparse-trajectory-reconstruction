# RQ2 FlightSketch data-curation protocol

## Purpose and scope

This protocol defines a results-blind audit of public FlightSketch rocket-flight time series
for a possible RQ2 on generalization to previously unseen rocket configurations. It is a data
feasibility and curation stage, not a model-selection or test-evaluation stage.

RQ1 remains closed and unchanged. No RQ1 test trajectory is used here.

## Source

- Public flight index: `https://flightsketch.com/flight-filter/`
- Public per-flight pages: `https://flightsketch.com/flights/<id>/`
- Public CSV downloads linked by each flight page
- Device documentation states 50 Hz recording of pressure, altitude, velocity, and, on newer
  units, three-axis acceleration.

The site exposes public downloads but no explicit dataset reuse or redistribution license was
found during the source audit. Raw CSV files may be cached locally for feasibility analysis,
but they must not be uploaded, redistributed, or packaged until written permission or a clear
license is obtained. Derived catalogs and aggregate quality statistics may be shared with full
source attribution and direct source URLs.

## Unit assumptions to verify

The public flight pages report altitude in feet and velocity in feet per second, and sampled
CSV maxima match those displayed values. Pressure appears in kPa. Accelerometer channels have
an approximately 32 ft/s^2 stationary magnitude, so they are provisionally interpreted as
ft/s^2. These interpretations remain provisional until confirmed by manufacturer documentation
or written clarification.

## Results-blind candidate selection

1. Parse all public index entries and retain the immutable FlightSketch numeric ID, title,
   description, and uploader label.
2. Form a conservative provisional vehicle key from uploader plus normalized title. Remove only
   explicit flight/run/launch number tokens and punctuation/spacing variation. Retain numbered
   parenthetical variants such as `(2)` because they may denote different physical airframes.
3. Do not use trajectory outcomes when forming vehicle keys.
4. Candidate groups must contain at least five indexed records.
5. To avoid domination by prolific vehicles, select at most twelve records per group using a
   deterministic SHA-256 ordering of the group key and flight ID.
6. Exclude obvious non-flight records whose title contains `chamber`, `vacuum`, `checkout`,
   `bench`, or `ground test`. Do not exclude generic `test flight` labels.

## Locked technical quality checks

A time series passes the automatic audit only if all conditions hold:

- CSV is downloadable and nonempty.
- Required columns `time`, `altitude`, and `velocity` exist.
- At least 250 data rows are present.
- At least 99% of required numeric cells are finite.
- At least 99.5% of adjacent timestamps are strictly increasing.
- Median sample interval is between 0.015 s and 0.25 s.
- Recorded duration is between 8 s and 300 s.
- Altitude span is between 50 ft and 100,000 ft.
- Maximum positive velocity is between 30 ft/s and 5,000 ft/s.
- The altitude maximum occurs after the detected launch and within the record.

Launch is detected as the first row at which either altitude exceeds its initial 2 s median by
5 ft or positive velocity exceeds 10 ft/s. Automatic pass/fail is followed by a blinded manual
review of diagnostic plots for the candidate split only; no model errors are available during
review.

## Configuration eligibility and split principles

- A provisional vehicle group becomes RQ2-eligible only if at least three of its selected
  records pass all automatic checks.
- All flights of one vehicle key must remain in a single outer split.
- The final train/validation/test assignment will be fixed before model fitting.
- Test groups will remain sealed until architecture, constraints, sparse masks, metrics, and
  training budget are frozen using train/validation only.
- A contributor-held-out sensitivity analysis will be specified because many public records may
  come from one uploader and share hardware or preparation practices.

## Planned outputs

- `source_index.csv`: public index catalog.
- `candidate_selection.csv`: deterministic, balanced pre-outcome sample.
- `flight_audit.csv`: per-flight technical checks and failure reasons.
- `vehicle_groups.csv`: aggregate group eligibility.
- `curation_summary.json`: machine-readable counts, thresholds, hashes, and caveats.
- `RQ2_DATA_CURATION_REPORT.md`: narrative feasibility conclusion.

No model training is authorized by this protocol.

## Post-audit decision addendum

The full audit produced 614 passing flights in 68 automatic groups, but 586 passing flights
(95.4%) and 64 groups came from one uploader label. Two group labels were nonidentifying, and 23
groups fell within eight possible variant-name families. Therefore automatic eligibility is only
a pilot-data screen. Physical-airframe/configuration identity must be confirmed and the intended
holdout unit must be frozen before any split or model fitting. A contributor-held-out analysis
may be reported only as a low-power sensitivity analysis, not as the primary generalization claim.
