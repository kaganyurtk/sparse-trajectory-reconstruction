# Version 0.9.0 prerelease notes

## Scope

This release candidate archives the reproducibility materials supporting the study "When kinematic constraints conflict with rocket telemetry: sparse trajectory reconstruction across two real-flight datasets."

## Included

- Complete RQ1 Falcon 9 training, validation, held-out evaluation, and verification code.
- Frozen RQ1 protocols, split records, audit reports, and integrity records.
- Iridium NEXT-5 diagnostic, constraint-ablation, and family leave-one-flight-out materials.
- Safe RQ2 FlightSketch source-audit, identity-review, deterministic split-preparation, and gate-verification utilities.
- Manuscript, Supplementary Information, citation metadata, and explicit reproducibility boundaries.

## Scientific interpretation

RQ2 reuses the matched NN and KC-NN model family and comparison logic developed for RQ1. It is a cross-dataset application of the same method, not a zero-shot evaluation of frozen Falcon 9 weights. The confirmatory RQ2 v1.1 analysis is an independent reconstruction and not the original pristine sealed test.

## Recovered experiment records

Recovered_Experiment_Records_v0.9.0.zip restores the original RQ1 final, NEXT-5 ablation, Iridium-family, and RQ2 reconstruction v1.1 packages, including runners, manifests, splits, saved checkpoints, predictions and historical verification records. See EXPERIMENT_RECORDS_README.md and RECOVERED_RECORDS_VERIFICATION.json. Permitted raw input data and configuration of historical paths are still needed for execution; no clean-environment full replay is claimed.

## Release boundary

Raw third-party telemetry is excluded. Original experiment records retain historical paths for provenance. Full numerical replay requires the permitted inputs and path configuration.

The 1 October saved-artifact audit (`OFFLINE_REPLAY_AUDIT_2026-10-01.md`) passed on the recovered records. The previously completed historical experiments and replay records remain the scientific results; no new training or raw-data replay is required to preserve or accurately report them. A fresh clean-environment raw-data replay would be an additional reproducibility check, not a condition for describing this v0.9.0 package as a historical-results release candidate.

The repository remains private until the author separately approves public visibility. Software and code are licensed under MIT; author-written prose and manuscript materials are licensed under CC BY 4.0. Third-party telemetry is outside both grants. No Zenodo record has been created. Public distribution of the manuscript and package should be checked separately from the validity of the already completed experiments.
