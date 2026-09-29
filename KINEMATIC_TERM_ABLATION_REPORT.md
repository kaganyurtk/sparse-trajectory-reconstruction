# Kinematic-term ablation report

## Scope

Exploratory post-hoc mechanism analysis using the frozen 5% mask, five paired seeds, the same
32x32 tanh architecture, learning rate, weight decay, 400-epoch budget, and unchanged
kinematic weight. Fifteen planned ablation runs completed; verification passed. This does not
replace the preregistered RQ1 result.

## Iridium NEXT-5 result

| Model / ablation | Five-seed composite | Change vs full KC-NN |
|---|---:|---:|
| NN | 0.2247 | +0.0752 |
| Full KC-NN | 0.1494 | +0.0000 |
| Remove `dh/dt >= 0` | 0.1385 | -0.0109 |
| Remove `dh/dt <= speed` | 0.3210 | +0.1716 |
| Remove `speed >= 0` | 0.1494 | +0.0000 |

## Interpretation

The `dh/dt <= speed` hinge is the decisive term. Removing it raises Iridium composite error
from 0.1494 to 0.3210, which is also worse than the NN value of
0.2247. All five seeds deteriorate. This term therefore explains the observed
KC-NN advantage far more strongly than the other two terms.

Removing `speed >= 0` changes the Iridium score by only +2.776e-17; the
resulting parameters match full KC-NN within 2.234e-15 absolute error.
The term was inactive in these runs. Removing `dh/dt >= 0` slightly improves the Iridium mean
to 0.1385; it is not responsible for the advantage and may add mild optimization cost
for this flight.

The conclusion remains mechanistic and post-hoc: `speed` is total speed, not vertical speed,
so `dh/dt <= speed` is a plausibility bound rather than an exact dynamical equation.
