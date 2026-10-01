# Reproducibility status

## Recovered and verified

Recovered_Experiment_Records_v0.9.0.zip restores the original RQ1 final, NEXT-5 ablation, Iridium-family, and RQ2 reconstruction v1.1 packages, including runners, manifests, splits, saved checkpoints, predictions and historical verification records. See EXPERIMENT_RECORDS_README.md and RECOVERED_RECORDS_VERIFICATION.json. Permitted raw input data and configuration of historical paths are still needed for execution; no clean-environment full replay is claimed.

The RQ1 inner split matches the deposited implementation. All 27 RQ2 archived checksum entries and all ten checkpoint hashes validate. The RQ2 manifest fingerprint matches the paper; its 46 test flight IDs and eight test groups match the split record, with pairwise separation from fitting and validation groups. Historical replay logs are retained and explicitly distinguished from the new integrity checks.

An additional saved-artifact audit on 1 October 2026 recomputed RQ1 per-flight metrics and scores from all 50 saved prediction files (726 rows each), matched all 50 saved weight hashes, loaded and exercised all ten RQ2 checkpoints on synthetic inputs, and independently checked RQ2 scores and five paired-seed differences. See OFFLINE_REPLAY_AUDIT_2026-10-01.md. This does not replace raw-telemetry metric replay.

## Additional reproducibility work and publication checks

- Supply permitted source telemetry and configure historical input paths.
- Assemble a clean execution environment; RQ1 records specify Python 3.12.14, NumPy 2.3.5 and PyTorch 2.7.1+cpu.
- Re-run the original verifiers only if claiming a new clean-environment, raw-telemetry end-to-end reproduction. This is not required to preserve and report the completed historical experiments.
- The current manuscript uses publicly accessible FlightSketch records and does not assert a separate research-permission grant. Raw third-party telemetry remains excluded; any later redistribution of the CSV files would require its own rights basis.

The repository and v0.9.0 Zenodo archive are public. Code is MIT; author-written documentation is CC BY 4.0. Third-party source material is outside these grants. The v0.9.0 archive DOI is 10.5281/zenodo.23080487; later version-specific DOIs must be cited separately.
