# RQ2 estimand and split protocol

## Locked scientific question

The primary RQ2 will measure sparse trajectory reconstruction on **previously unseen confirmed
vehicle/configuration groups within the dominant contributor's operating regime**. It will not be
described as broad cross-operator or orbital-launch-vehicle generalization.

The holdout unit is a confirmed canonical vehicle/configuration ID. Public title groups are only
provisional inputs to that identity review. Flights belonging to one canonical ID may never cross
train, validation, or test boundaries.

## Cohorts

1. **Primary in-domain cohort:** confirmed groups from the dominant contributor. This cohort is
   used for the main group-held-out train/validation/test experiment.
2. **External contributor sensitivity cohort:** all confirmed groups from other contributors.
   These groups remain sealed and are reported descriptively because their count is too small for
   a strong contributor-generalization estimate.
3. **Excluded records:** nonidentifying groups that cannot be resolved, ambiguous groups without
   adequate evidence, explicit non-flight records, and failed technical-quality records.

## Identity gate

Every row in `identity_review_template.csv` must receive one of:

- `confirmed_same_airframe`
- `confirmed_configuration_group`
- `exclude`

Every included row must also receive a canonical vehicle ID and an evidence source. The split code
refuses to write any split while a decision is pending or an included canonical ID is missing.

## Deterministic allocation

After identity review, canonical primary-cohort IDs are ordered by SHA-256 of the fixed seed
`rq2-flightsketch-v1-identity-gated` and the canonical ID. Approximately 15% are assigned to sealed
test, 15% to validation, and the remainder to train, with at least three groups in validation and
test. The algorithm, seed, and eligibility rules are frozen before model fitting.

All non-dominant-contributor groups are assigned to a separate sealed external-sensitivity cohort.
They are not used for hyperparameter tuning.

## Test firewall

- Test and external-sensitivity trajectories are not plotted or summarized beyond metadata counts
  until preprocessing, sparse masks, baselines, architecture, physical constraints, metrics, seed
  policy, and tuning budget are frozen using train/validation only.
- Test failures are reported; they do not trigger model changes.
- RQ1 test trajectories remain unrelated and inaccessible to the RQ2 pipeline.

## Current state

The identity review has not been completed. Therefore no final split exists and model fitting is
blocked by design.

