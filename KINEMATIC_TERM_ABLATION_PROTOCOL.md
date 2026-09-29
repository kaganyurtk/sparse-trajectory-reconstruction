# Post-hoc kinematic-term ablation protocol

## Status and purpose

This is an exploratory mechanism analysis requested after RQ1 was closed. It does not replace
the preregistered RQ1 analysis and is not used to tune or revise the selected models. The sole
purpose is to identify which term of the frozen KC-NN inequality penalty is associated with the
unusually strong Iridium NEXT-5 result.

## Locked design

- Training data: the original 28 training flights and the frozen 5% observation mask.
- Evaluation data: the six outer-validation flights and six held-out test flights. Test results
  are explicitly post-hoc and descriptive.
- Seeds: 11, 29, 47, 71, and 97.
- Architecture and optimizer: unchanged 32x32 tanh network, Adam, learning rate 0.001,
  weight decay 0.0001, exactly 400 epochs, no checkpoint selection.
- Kinematic weight: unchanged at 33.6822579609781 for every ablation.
- Baselines: reuse the already-frozen NN and full KC-NN results; do not retrain them.
- No hyperparameter or term-weight adjustment is permitted after viewing results.

The full KC-NN penalty is the mean squared sum of three hinge terms:

1. `vertical_rate_nonnegative = relu(-dh_dt / speed_scale)`
2. `vertical_rate_le_speed = relu((dh_dt - speed) / speed_scale)`
3. `speed_nonnegative = relu(-speed / speed_scale)`

Three ablations are trained, each removing exactly one term while keeping the other two and
all other settings fixed:

- `omit_vertical_rate_nonnegative`
- `omit_vertical_rate_le_speed`
- `omit_speed_nonnegative`

## Interpretation rule

The primary descriptive diagnostic is the five-seed mean standardized composite error on
Iridium NEXT-5 at 5% observations. A removed term is considered a plausible driver if its
removal consistently erodes the full KC-NN advantage relative to NN. All-flight metrics,
per-seed results, altitude/speed decomposition, and inequality-component activity are reported
as secondary diagnostics. No p-value or independent-seed inference is planned.

