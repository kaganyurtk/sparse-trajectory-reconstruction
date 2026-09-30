# Sparse trajectory reconstruction under kinematic constraints

Reproducibility workspace for the manuscript:

> **When kinematic constraints conflict with rocket telemetry: sparse trajectory reconstruction across two real-flight datasets**

**Author:** Kağan Yurtkölesi  
**Affiliation:** Department of Aerospace Engineering, Izmir University of Economics, Izmir, Türkiye

## Scope

The study compares matched unconstrained neural networks (NN) and kinematically constrained neural networks (KC-NN) for sparse reconstruction of altitude and speed/velocity trajectories.

- **RQ1:** 40 Falcon 9 flights; 28 training, 6 outer-validation, and 6 held-out test flights.
- **RQ2:** an independent FlightSketch reconstruction with a confirmatory v1.1 group-held-out evaluation.
- **Primary observation condition:** 5% of each trajectory, with deterministic matched masks.
- **Paired seeds:** 11, 29, 47, 71, and 97.

The main scientific conclusion is deliberately conditional: a constraint can reduce kinematic violations without improving predictive generalization when the measured channels do not match the assumed physical relation.

## Repository status

This repository is currently a **private v1.0.0 release candidate**. It contains the manuscript, Supplementary Information, frozen protocols, integrity records, complete RQ1 experiment code, and the safe RQ2 preparation utilities recovered from the project archive. It has not yet been made public or archived with Zenodo.

See [`REPRODUCIBILITY_STATUS.md`](REPRODUCIBILITY_STATUS.md) for the boundary between verified contents and items still required before a public release.

## Included materials

- `Acta_Astronautica_Manuscript.docx` — current manuscript.
- `Acta_Astronautica_Supplementary_Information.docx` — supplementary methods and results.
- `INTEGRITY_RECORDS.json` — frozen fingerprints and replay status reported in the paper.
- `rq1_ablation_manifest.json` — locked NEXT-5 constraint-ablation configuration.
- `iridium_family_lofo_manifest.json` — locked Iridium-family leave-one-flight-out configuration.
- `iridium_family_lofo_summary.json` and `iridium_family_lofo_verification.json` — derived run and replay records.
- `analyze_iridium_advantage.py` and `verify_and_report_kinematic_ablation.py` — targeted RQ1 diagnostic utilities.
- `prepare_rq2_split.py` and `verify_rq2_gates.py` — RQ2 identity-gated split utilities.
- `rq1_training/` — complete RQ1 training, validation, held-out evaluation, and verification code.
- `rq2/` — recovered shareable RQ2 source-audit, identity-review, and split-preparation utilities.
- Protocol and audit Markdown files documenting the analyses and their limitations.

## Data availability boundary

Raw third-party FlightSketch CSV files are **not included**. Public-source access does not automatically imply redistribution permission. A public release must follow the written authorization and attribution requirements applicable to those files. Derived metadata may be released only after a final privacy, provenance, and permission check.

The included scripts may refer to artifacts from the original analysis workspace that are not yet deposited. Their presence documents the verified analysis logic; it does not imply that the repository is already executable end to end.

## Reproduction outline

1. Reconstruct the permitted input datasets and verify source hashes.
2. Apply the frozen flight/group splits and deterministic masks.
3. Fit paired NN and KC-NN models with identical architecture, observations, and seeds.
4. Replay saved checkpoints and verify predictions and reported aggregate metrics.
5. Confirm the manifest fingerprints listed in `INTEGRITY_RECORDS.json`.

The RQ1 environment is pinned in `rq1_training/requirements.txt`. The historical RQ2 model-fitting/evaluation runner was not present in the recovered shareable archive; the release metadata and RQ2 README state this limitation explicitly rather than claiming end-to-end RQ2 reproducibility.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). A DOI will be added after the verified `v1.0.0` release is archived with Zenodo.

## License

Software and code are licensed under the [MIT License](LICENSE). The author-written manuscript, Supplementary Information, protocols, reports, and other prose documentation are licensed under [CC BY 4.0](DOCUMENTATION_LICENSE.md). See [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md) for the exact boundary.

These licenses do not cover third-party telemetry or other externally owned material. Such material remains governed by its original terms and any written authorization.
