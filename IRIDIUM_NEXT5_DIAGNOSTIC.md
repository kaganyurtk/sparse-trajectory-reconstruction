# Iridium NEXT-5 KC-NN diagnostic

This is a post-hoc read-only analysis of frozen RQ1 outputs. No model was trained or tuned.

## Main finding

At 5% observations, mean composite error is 0.2247 for NN and
0.1494 for KC-NN. KC-NN is better for all five paired seeds.
About 79.5% of the composite improvement comes from altitude RMSE:
the five-seed mean falls from 2260.3 m to
933.8 m. Speed RMSE falls more modestly from
78.88 to 68.96 m/s and improves
for four of five seeds.

The seed-mean NN trajectory overshoots the true altitude after roughly 30 s, with its largest
error in the 61–90 s window. KC-NN substantially suppresses that overshoot. Its approximate
finite-difference inequality-violation fraction is
5.8%, versus
38.0% for NN.

## Observation-rate sensitivity

| Training observations | NN | KC-NN | KC-NN minus NN |
|---:|---:|---:|---:|
| 100% | 0.1641 | 0.1046 | -0.0595 |
| 50% | 0.1378 | 0.0930 | -0.0448 |
| 25% | 0.1689 | 0.1130 | -0.0559 |
| 10% | 0.1974 | 0.1311 | -0.0663 |
| 5% | 0.2247 | 0.1494 | -0.0752 |

The advantage exists even at 100% and grows as training becomes sparser. It is therefore not
specific to one 5% mask.

## Most plausible explanation

The network input does not include mission identity or orbit. Iridium NEXT-5 appears only as
time + Block 4 + 9,600 kg payload. Its closest training point in that encoded static feature
space is Iridium NEXT-3 (Block 4, 8,600 kg); the exact Block-4/9,600-kg combination is absent.
The unconstrained NN extrapolates this combination into an overly high middle/late altitude
curve. The inequality penalty behaves like a trajectory-shape regularizer and prevents most
of that overshoot. This mechanism is strongly supported descriptively, but it is not a causal
proof because the post-hoc analysis does not intervene on individual constraint terms.

## Important caveat

The KC-NN penalty enforces `0 <= dh/dt <= total speed` and nonnegative speed. Total speed is
not vertical speed, so this is a weak plausibility inequality rather than an exact kinematic
equation. Altitude telemetry is quantized, which also makes pointwise finite differences noisy.
