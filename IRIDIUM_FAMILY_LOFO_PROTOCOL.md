# Iridium-family leave-one-flight-out replication protocol

## Scientific status

This study is a post-hoc replication prompted by the Iridium NEXT-5 mechanism analysis after
the preregistered RQ1 study was closed. It does not alter the RQ1 primary result. The hypothesis
and decision rule below are locked before any leave-one-flight-out model is trained.

## Question

Does the KC-NN upper-bound hinge `dh/dt <= total speed` provide a repeatable advantage across
other Iridium NEXT flights, or was the Iridium NEXT-5 result flight-specific?

## Fixed folds and data boundary

The five Iridium missions in the original 28-flight training partition are each held out once:

- `iridium_next_1`
- `iridium_next_3`
- `iridium_next_4`
- `iridium_next_6`
- `iridium_next_8`

Each fold trains on the other 27 original training flights and evaluates on the full 121-row
trajectory of the held-out Iridium flight. The six original test trajectories, including
Iridium NEXT-5, are forbidden as inputs to training, selection, normalization, or fold
evaluation. Existing frozen Iridium NEXT-5 results may be displayed only after the five-fold
decision is computed.

## Frozen training settings

- Training observations: original frozen 5% mask, with the held-out flight removed.
- Seeds: 11, 29, 47, 71, 97.
- Architecture: 32x32 tanh trajectory network.
- Optimizer: Adam, learning rate 0.001, weight decay 0.0001.
- NN epochs: 560, matching the selected RQ1 NN setting.
- Full KC-NN epochs: 400, matching the selected RQ1 KC-NN setting.
- Upper-bound-only KC-NN epochs: 400.
- Kinematic weight: fixed at 33.6822579609781; no recalibration by fold or variant.
- No early stopping, checkpoint selection, hyperparameter search, or post-result adjustment.

The three fitted variants are:

1. `nn`: data loss only.
2. `full_kcnn`: all three original hinges (`dh/dt >= 0`, `dh/dt <= speed`, `speed >= 0`).
3. `upper_bound_only`: only `dh/dt <= speed`.

This yields 5 folds x 3 variants x 5 seeds = 75 planned runs.

## Primary estimand and locked decision rule

For each held-out flight, compute the five-seed mean standardized composite error
`0.5 * (altitude_RMSE / fold_training_altitude_scale + speed_RMSE / fold_training_speed_scale)`.
The primary contrast is `upper_bound_only - nn`; negative values favor the constrained model.

The family-level hypothesis is considered internally replicated only if:

1. `upper_bound_only` beats `nn` on at least four of the five held-out flights, and
2. the unweighted mean of the five flight-level differences is negative.

Otherwise, the Iridium NEXT-5 mechanism remains a flight-specific post-hoc observation.
Full KC-NN comparisons, altitude/speed decomposition, paired-seed variability, and the
previously observed Iridium NEXT-5 result are secondary/descriptive.

