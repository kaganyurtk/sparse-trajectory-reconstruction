# Release audit for private v0.9.0 candidate

## Recovery correction

An initial audit of the narrow shareable packages missed the full experiment archives. A subsequent Drive and project-file search recovered them. The earlier missing-runner, missing-split and missing-checkpoint findings are superseded by the following record.

Recovered_Experiment_Records_v0.9.0.zip restores the original RQ1 final, NEXT-5 ablation, Iridium-family, and RQ2 reconstruction v1.1 packages, including runners, manifests, splits, saved checkpoints, predictions and historical verification records. See EXPERIMENT_RECORDS_README.md and RECOVERED_RECORDS_VERIFICATION.json. Permitted raw input data and configuration of historical paths are still needed for execution; no clean-environment full replay is claimed.

## Checks completed

- Author and version metadata checked.
- JSON/CFF parsing and Python syntax checked.
- Offline RQ2 synthetic gate test passed.
- Portable Iridium manifest hash validated separately from historical hashes.
- Original RQ2 archive checksum list: 27 entries passed.
- RQ2 saved model hashes: ten passed.
- RQ2 final manifest, test IDs and group separation validated.
- RQ1 inner split agrees with the historical record.
- CRediT and research-permission statements completed from the author instructions.
- Saved-artifact audit on 1 October: 50 RQ1 prediction files and weight hashes verified, per-flight metrics and scores recomputed; ten RQ2 checkpoints loaded and exercised on synthetic inputs, summary arithmetic independently checked. See OFFLINE_REPLAY_AUDIT_2026-10-01.md.

## Boundaries

These are integrity and saved-artifact consistency checks, not new model training or full raw-telemetry metric replay. Historical scripts retain their original workspace paths; source data and path configuration are needed for execution. The repository remains private pending public-release preparation and manuscript-distribution review.
