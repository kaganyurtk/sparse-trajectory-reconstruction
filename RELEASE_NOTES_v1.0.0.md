# v1.0.0 release notes

This release supersedes the v0.9.0 working archive as the current documented reproducibility package for the manuscript *When kinematic constraints conflict with rocket telemetry: sparse trajectory reconstruction across two real-flight datasets*.

## Changes since v0.9.0

- Updated the manuscript and Supplementary Information to describe the archived RQ2 v1.1 implementation precisely: FlightSketch-specific fitted weights, sparse reconstruction inputs with complete fitting targets, and the centered-velocity residual offset of approximately −0.00041023. The offset-corrected model was not tested.
- Replaced an unsupported assertion of separate FlightSketch research permission with the verifiable fact that the analyzed records and CSV downloads are publicly accessible. Raw third-party CSV files remain outside this package; public access is not represented as a redistribution license.
- Included the submission working copy, figures, highlights, cover-letter draft, and author-review checklist. The paper has not been submitted to Acta Astronautica.
- Retained the original runners, final splits, saved checkpoints, predictions, historical verification records, and the October 1 offline saved-artifact audit. No new model training was performed and numerical results are unchanged.

## Evidence boundary

The archive supports source-code inspection, saved-artifact integrity checks, RQ1 saved-prediction metric recomputation, RQ2 checkpoint loading on synthetic inputs, and RQ2 summary arithmetic verification. It does not demonstrate a fresh end-to-end replay from the third-party raw telemetry in a clean environment. Such a claim would require obtaining the public source data, configuring historical paths, and running the original verifiers. The RQ1 and RQ2 observation protocols are distinct, and this is not a controlled transfer-learning test.

Code is MIT-licensed; author-written prose is CC BY 4.0. Neither grant covers third-party data. Cite the version-specific Zenodo DOI assigned to this v1.0.0 archive once published; the earlier v0.9.0 DOI is 10.5281/zenodo.23080487.
