# v1.0.0 release audit

## Scope

This is a documentation and packaging release. It does not change the archived model weights, numerical results, flight splits, masks, or original experiment runners. The v0.9.0 GitHub tag and Zenodo record remain immutable.

## Scientific checks

- RQ1 uses sparse fitting labels on 40 Falcon 9 flights; RQ2 reconstruction v1.1 uses sparse inputs and complete fitting labels on public FlightSketch records.
- RQ2 trained dataset-specific weights rather than transferring Falcon 9 checkpoint weights.
- The RQ2 archived kinematic residual omits the velocity mean, producing an approximate normalized offset of −0.00041023. No corrected-residual experiment is claimed.
- NEXT-5 benefit is post-hoc and did not satisfy the locked Iridium-family replication criterion.
- Prior saved-artifact and checksum audits are retained; no clean-environment full raw-data replay is claimed.

## Source and rights boundary

FlightSketch flight pages provide public CSV downloads. No separate research-permission attestation is made in the current submission drafts. No raw third-party CSV is included or relicensed. Source links and contributor attribution are retained. The manuscript and Supplementary Information are author-written prose under CC BY 4.0; code is MIT.

## Journal boundary

The cover letter and checklist are working documents. Journal-specific submission checks and the author's final review remain outstanding. This release is not a journal submission.
