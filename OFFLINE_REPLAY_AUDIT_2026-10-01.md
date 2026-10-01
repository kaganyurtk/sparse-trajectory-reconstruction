# Offline saved-artifact audit — 1 October 2026

This is a new, independent check of the recovered **saved artifacts**. It is not a clean-environment replay from third-party source telemetry and does not constitute new model training.

## Checks run

- RQ1: all 50 held-out model weight hashes matched their recorded SHA-256 values. Each of the 50 saved prediction files contained 726 rows (six flights × 121 rows). Altitude and speed RMSE/MAE were recomputed for every flight directly from the saved true/predicted columns. Per-flight RMSEs, their means and standardized evaluation scores matched the saved per-run records and aggregate entries. The test manifest fingerprint independently recomputed to `89728925fd31f436dbb9438556157e7a030ce7ee881b557cdad434257b2fa64b`.
- RQ2: all ten saved `.npz` files matched the historical checkpoint SHA-256 values, contained the expected six tensors for a 7–32–32–2 network, and produced finite outputs on a synthetic input. Each combined score was recalculated from the reported two RMSEs and fit-only target scales. All five seed-paired differences, mean difference (`+0.1048728933655938`), standard deviation, and 0/5 KC-NN wins matched the results file. The manifest fingerprint independently recomputed to `9efc8c68fc63ac7603e471e101571417017ac5bfb51398fa2f718396761f8782`.
- The RQ2 identity-gate synthetic fixture passed all seven checks; it wrote no production split and performed no training.

## What remains untested

The saved RQ2 checkpoints were **not** evaluated against raw FlightSketch trajectories in this audit. The required 614-file source snapshot (including the 46 held-out test flights) is not in the recovered package or accessible Drive shareable materials. The archived `verification.json` reports a historical exact metric replay, but that report is historical evidence, not a result newly reproduced here. RQ1's saved predictions were checked against their saved truths, but RQ1 model outputs were not regenerated from raw telemetry.

The original experiments and historical replay records can be reported as completed. To additionally claim a **new clean-environment end-to-end reproduction**, supply authorized source input files, validate source hashes, configure historical paths, then run the original replay verifiers. The private v0.9.0 candidate must retain the distinction between historical verification and this new saved-artifact audit. Do not distribute third-party raw telemetry without explicit redistribution authorization.

Audit runner: `offline_replay_audit.py` (uses NumPy; no training dependencies). The run completed successfully on 1 October 2026.
