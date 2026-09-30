# Reproducibility status

## Verified and included

- Current manuscript and Supplementary Information.
- RQ1 and Iridium-family locked configuration records.
- RQ1 NEXT-5 diagnostic, ablation, and family-transfer protocols/reports.
- RQ2 curation, estimand, split-gate, and operational-identity protocols.
- Available diagnostic and split-verification scripts.
- Frozen analysis fingerprints and reported replay checks.
- Complete RQ1 training, validation, held-out evaluation, and verification code under `rq1_training/`.
- Recovered shareable RQ2 source-audit, identity-review, and split-preparation utilities under `rq2/`.

## Required before public `v1.0.0`

- Recover or reconstruct and validate the historical RQ2 model-fitting/evaluation runner; until then, retain the explicit partial-reproducibility statement.
- Confirm whether the RQ1 pinned requirements are sufficient for the final environment record and add platform details if available.
- Add the machine-readable RQ1 inner split and final RQ2 v1.1 split record.
- Add or regenerate the final RQ1 and RQ2 manifests whose fingerprints appear in `INTEGRITY_RECORDS.json`.
- Re-run the package from a clean environment and record commands and outputs.
- Confirm the written FlightSketch permission and required attribution language.
- Remove absolute/local paths and any nonportable workspace references from released records.
- Review manuscript-distribution rules before including the submitted manuscript in the public Zenodo record.

## Licensing resolved for the release candidate

- Software and code: MIT License.
- Author-written manuscript and documentation: CC BY 4.0.
- Third-party telemetry and externally owned material: excluded from both grants and governed by their original terms.

## Explicit exclusions

- Raw FlightSketch CSV files are not deposited.
- No claim is made that the current private draft is executable end to end.
- The RQ2 v1.1 evaluation is a confirmatory reconstruction, not a pristine sealed test.
- The repository must remain private until the author separately approves public visibility.
