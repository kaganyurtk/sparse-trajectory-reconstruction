# Zenodo metadata for version 1.0.0

This file records the intended metadata for the first archived software release. `CITATION.cff` remains the machine-readable source used by the GitHub-Zenodo integration.

## Record

- Resource type: Software
- Title: Sparse trajectory reconstruction under kinematic constraints
- Version: 1.0.0
- Release date: 2026-09-30
- Creator: Tek Kağan Yurtkölesi
- Affiliation: Department of Aerospace Engineering, Izmir University of Economics, Izmir, Türkiye
- Repository: https://github.com/kaganyurtk/sparse-trajectory-reconstruction
- Language: English

## Description

Reproducibility materials for matched unconstrained and kinematically constrained neural-network studies of sparse rocket-trajectory reconstruction across Falcon 9 webcast telemetry and public FlightSketch records. The package contains complete RQ1 training, validation, held-out evaluation, and verification code, plus safe RQ2 data-curation and split-preparation utilities. Raw and processed third-party telemetry, trained model weights, generated prediction trees, and the unavailable historical RQ2 model-fitting/evaluation runner are excluded. The release therefore supports complete inspection of the RQ1 implementation and partial inspection of the RQ2 preparation workflow without claiming end-to-end RQ2 numerical reproducibility.

## Keywords

- rocket telemetry
- trajectory reconstruction
- physics-informed machine learning
- kinematic constraints
- sparse observations
- reproducibility

## Access and licensing

The intended access right is open after the repository passes the final release audit and the author approves public visibility. Software and code use the MIT License. Author-written manuscript and documentation use CC BY 4.0. Third-party telemetry is not included and is not covered by either license.

## Publication relationship

Associated manuscript: "When kinematic constraints conflict with rocket telemetry: sparse trajectory reconstruction across two real-flight datasets" by Tek Kağan Yurtkölesi (2026). Add the journal DOI as `isSupplementTo` only after a DOI exists.
