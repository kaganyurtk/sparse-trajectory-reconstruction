# Release audit for private v0.9.0 candidate

Audit date: 2026-09-30

This record describes the inspected private repository state. It is not a claim that every reported experiment can currently be reproduced end to end.

## Passed checks

- Author metadata consistently identifies Kağan Yurtkölesi, Department of Aerospace Engineering, Izmir University of Economics, Izmir, Türkiye.
- Release-candidate metadata uses version `0.9.0`; no DOI or release date is claimed.
- `CITATION.cff` parses as YAML and identifies the MIT software license.
- All inspected JSON files parse successfully.
- All Python files pass syntax compilation.
- `verify_rq2_gates.py` passes its offline synthetic-fixture checks without creating or using production telemetry.
- The portable `iridium_family_lofo_manifest.json` fingerprint validates as `7fa55ac8b8fd26e6d3d002064f07b3352847e198072a9cf59ef14366b665bf9c`.
- `MANIFEST_PROVENANCE.json` records why this portable fingerprint differs from the historical path-dependent fingerprint.
- The manuscript renders cleanly as 13 pages after the data-and-code availability statement was corrected.
- A repository scan found no common credential or private-key patterns in the release candidate.

## Partial checks and limitations

- The RQ1 source implementation is present, but a full clean-environment training replay was not run during this audit because the input data are excluded and PyTorch is not installed in the audit environment.
- Root diagnostic scripts require excluded frozen `outputs/` trees. Their syntax and import structure were checked, but the historical analyses were not recomputed.
- The historical RQ2 model-fitting/evaluation runner, NEXT-5 ablation runner, and Iridium-family training runner were not found in the inspected archive.
- The final RQ2 v1.1 production split artifact and its manifest are not included. The RQ2 gate test uses a clearly identified synthetic fixture only.

## Required before public publication or journal submission

- Replace the manuscript's CRediT placeholder with author-approved contribution roles.
- Replace the manuscript's ethics/permissions placeholder with the exact statement supported by the written FlightSketch authorization, including any required attribution.
- Confirm the journal/preprint distribution terms for the manuscript file before making the repository or Zenodo record public.
- Either recover the missing historical runners and artifacts or retain the package's explicit partial-reproducibility language.
- Run the available package in a clean pinned environment once the permitted inputs are assembled, and archive the command log.

The repository should remain private until these author-controlled and source-permission items are resolved.
