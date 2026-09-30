# Version 1.0.0 release notes

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

## Excluded

- Raw or processed third-party FlightSketch trajectories.
- Trained model weights and generated prediction trees.
- Credentials, local environments, caches, and machine-specific paths.
- The historical RQ2 model-fitting/evaluation runner, which was not present in the recovered shareable archive.

## Release boundary

RQ1 source-level and end-to-end experiment logic is included, but reproducing its numerical outputs requires authorized processed telemetry. RQ2 curation and split preparation are included; the numerical RQ2 results are not claimed to be end-to-end reproducible from this repository alone.

The repository remains private until the author separately approves public visibility. Software and code are licensed under MIT; author-written prose and manuscript materials are licensed under CC BY 4.0. Third-party telemetry is outside both grants. No Zenodo record or GitHub release should be published before the manuscript-distribution status and remaining release checks are resolved.
