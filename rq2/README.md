# RQ2 FlightSketch preparation utilities

This directory contains the shareable RQ2 source-audit, identity-review, and deterministic split-preparation utilities recovered from the frozen Google Drive package.

RQ2 uses the same matched NN and KC-NN model family and comparison logic as RQ1. It does not define a new model architecture. The FlightSketch analysis does, however, use its own fit and validation partitions, fit-only scaling, deterministic sparse-observation masks, and paired optimization seeds. Accordingly, it should be described as a cross-dataset application of the RQ1 method rather than a zero-shot reuse of frozen Falcon 9 weights.

## Included workflow

```bash
python build_flightsketch_catalog.py --output-dir outputs/flightsketch_audit
python verify_flightsketch_audit.py --output-dir outputs/flightsketch_audit
python summarize_flightsketch_audit.py --output-dir outputs/flightsketch_audit
python build_identity_review.py --audit-dir outputs/flightsketch_audit
python verify_rq2_gates.py
```

`prepare_rq2_split.py` is identity-gated. It must not write a split while a review row remains pending or an included group lacks a canonical vehicle identifier.

## Scientific and redistribution boundary

The original RQ1 final, NEXT-5 ablation, Iridium-family and RQ2 reconstruction v1.1 packages have now been recovered in `../Recovered_Experiment_Records_v0.9.0.zip`. This includes the RQ2 runner, final split, checkpoints and historical verification records. See the repository-root `EXPERIMENT_RECORDS_README.md`. Execution still requires permitted source data and configuration of historical paths; a clean-environment end-to-end replay has not been performed.

Raw and processed FlightSketch trajectories are intentionally excluded. Do not add third-party trajectory files unless their redistribution is explicitly authorized and the required attribution and provenance records are retained.
