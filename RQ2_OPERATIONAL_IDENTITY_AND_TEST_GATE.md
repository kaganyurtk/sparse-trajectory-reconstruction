# RQ2 operational identity and final-test gate — v2

Date: 2026-09-23  
Scope: FlightSketch RQ2 identity policy, development-cohort traceability, and final-test firewall  
Source status (2026-10-02 clarification): **public FlightSketch pages and CSV downloads; no separate research-permission attestation is made in the v1.0 release**  
Trajectory release in this artifact: **none**  
Final-test status: **not created, not accessed, not assigned**

## Decision

Public uploader and flight-title metadata do not establish physical airframe identity. RQ2 must therefore not claim evaluation on “confirmed vehicles” or “confirmed configurations” unless first-party identity metadata is obtained. The defensible operational unit remains a **provisional uploader + normalized-title group**.

The earlier `RQ2_ESTIMAND_AND_SPLIT_PROTOCOL.md` is too strong where it requires `confirmed_same_airframe` or `confirmed_configuration_group` decisions from public titles alone. That confirmation requirement is superseded for current work by this conservative policy. Existing development results are not recomputed or relabelled.

## Evidence reviewed

- 4,040 indexed records; 617 deterministic candidates; 614 quality-pass records.
- 68 provisional uploader-title rows in the identity review register.
- 64 rows and 586 passing records belong to the dominant uploader label.
- The frozen development result reports 41 provisional groups, 335 flights, 33 train groups, 8 outer-validation groups, and 0 test groups.
- The Drive folder contains development summary results but no exact 41-group name manifest or fit/inner/outer group-name manifest.
- Exactly 41 dominant-uploader source rows have at least 8 quality-pass records. This is a useful reconstruction clue, but it is an inference and not a substitute for the missing manifest.

## Operational grouping policy

1. Retain uploader-title rows as provisional operational groups; do not infer physical identity.
2. Exclude two nonidentifying titles from identity-based evaluation:
   - `alane, lane::2021-09-05_v2_e12-4`
   - `gtg738w, russ::test flight`
3. Consolidate only formatting-level aliases within the same uploader. Five alias families were identified:
   - `alpha iii (6)` / `alpha iii(6)`
   - `checkmate (2)` / `checkmate(2)`
   - `checkmate (3)` / `checkmate(3)`
   - `nova payloader (4)` / `nova payloader(4)`
   - `nova payloader(2)` / `novapayloader(2)`
4. Keep numbered variants distinct unless first-party evidence proves equivalence. Examples include `alpha iii (6)` versus `alpha iii (8)`, and `nova payloader (4)` versus `(5)` or `(6)`.
5. Keep non-dominant-uploader groups sealed as external-contributor sensitivity candidates.

This policy yields 66 retained source rows and 61 unique operational groups after formatting-only consolidation. Physical identities confirmed: **0**.

## Development-cohort implication

Four of the five alias families contain two source rows that are both consistent with the inferred “dominant uploader + at least 8 passing records” development rule. The fifth family contains one row above and one below that threshold. If any alias pair crossed fit, inner-validation, or outer-validation boundaries, the original development split may contain operational-unit leakage.

No conclusion about leakage is made without the exact historical assignments. The existing numerical results remain labelled development evidence. They must not be treated as final-test evidence.

## Final-test firewall

The final-test gate remains closed. No test split may be produced from the current files because the exact development membership is not independently recoverable from a sealed manifest.

Before any test assignment:

1. Recover the exact 41-group development manifest and the fit/inner/outer assignments from the original experiment environment or an authoritatively preserved run artifact.
2. Hash that manifest and store the hash with the method-freeze record.
3. Audit the five alias families across the historical boundaries.
4. Define the eligible candidate pool using metadata only; do not load, summarize, plot, or score candidate trajectories.
5. Freeze the candidate allocation algorithm, seed, exclusions, and reporting rules.
6. Create and seal the final-test manifest; open it only for the single frozen evaluation.

If the exact development manifest cannot be recovered, the scientifically clean option is to rebuild RQ2 from scratch with a new versioned split. In that case, all previously inspected groups remain development-only and cannot enter the new final test.

## Controlled artifact

- Workbook: `RQ2_IDENTITY_DECISION_REGISTER_v2_2026-09-23.xlsx`
- Workbook SHA-256: `ec4bc47d601a78c0bfbff7596fbc3f7049c8bcf3205f6469c273acf162bcb3a4`
- Workbook contents: aggregate identity metadata, operational decisions, alias audit, and source evidence fields only; no raw or processed trajectories.

## Change control

This document changes claim scope and gate logic only. It does not change the frozen neural architecture, optimizer, seeds, masks, metrics, physics residual, development results, or reference-model decision. It does not modify the manuscript.
