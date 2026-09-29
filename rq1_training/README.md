# RQ1 Reproducibility Package

This repository contains the training, validation, and held-out test evaluation code for **RQ1** of the study *Physics-Informed Neural Networks for Rocket Trajectory Prediction: Limited-Data Learning and Cross-Vehicle Generalization*.

RQ1 compares a data-driven neural network (NN) with a kinematically constrained neural network (KC-NN) for predicting Falcon 9 altitude and speed during the first 120 seconds of flight under limited observations. Both methods use the same 32×32 `tanh` architecture, inputs, initialization, optimization budget, and data masks. KC-NN adds the physically valid inequality constraint

```text
0 <= dh/dt <= v,  v >= 0
```

where `v` is speed magnitude rather than vertical speed.

## Repository contents

- `experiment.py`: model, loss functions, data loading, training, and metrics.
- `run_experiment.py`: preregistered smoke and full 98-run experiment.
- `test_experiment.py`: implementation and leakage-safety checks.
- `evaluate_test.py`: one-time evaluation of frozen models on six held-out flights.
- `verify_*.py`: output and replay verification.
- `diagnose_validation.py`: validation diagnostics.
- `inner_split.json`: frozen 22/6/6 inner/outer split definition.
- `RQ1_EXPERIMENT_PROTOCOL.md`: frozen experimental protocol.
- `docs/`: reports and evaluation documentation retained from the completed experiment.
- `data/README.md`: required data layout and schema.

Generated predictions, model weights, processed telemetry, and other bulky run artifacts are intentionally excluded from this code package.

## Environment

Python 3.11 or a compatible recent Python 3 release is recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The pinned requirements install the CPU build of PyTorch.

## Data preparation

The public code package does not redistribute telemetry. Prepare authorized processed data using the exact directory structure and CSV schema described in [`data/README.md`](data/README.md). The experiment expects 28 training flights, 6 outer-validation flights, and the five nested observation masks.

## Validation checks

After preparing the training and validation data:

```bash
python test_experiment.py
```

These checks verify the split, nested masks, deterministic paired initialization, automatic differentiation, chain-rule scaling, train-only kinematic-weight calibration, and test-set isolation.

## Smoke run

```bash
python run_experiment.py \
  --mode smoke \
  --smoke-epochs 5 \
  --protocol RQ1_EXPERIMENT_PROTOCOL.md
python verify_outputs.py
```

Smoke output is written to `outputs/smoke_v2/` and is not a scientific result.

## Full RQ1 experiment

```bash
python run_experiment.py \
  --mode full \
  --protocol RQ1_EXPERIMENT_PROTOCOL.md
python verify_full_outputs.py
```

The full plan consists of 48 inner-screening trainings and 50 final refits. Completed runs are reused only when the saved fingerprint and weight hash match the current code, protocol, split, masks, and data.

## Held-out test evaluation

The test evaluation requires the verified frozen outputs from the full experiment and exactly six authorized test-flight CSV files. See `TEST_EVALUATION_PROTOCOL.md` and `data/README.md` before running:

```bash
python evaluate_test.py
python verify_test_outputs.py
```

Do not use held-out test results to change the model, constraint, preprocessing, or hyperparameters.

## Reproducibility boundary

This release provides the complete experiment code but not the processed telemetry or trained weights. Consequently, source-level and synthetic checks can be inspected immediately, while end-to-end numerical reproduction requires authorized copies of the frozen processed data. The study covers only the early-ascent interval from T+0 to T+120 seconds and should not be interpreted as full-flight or orbital prediction.

## Citation

Citation metadata is provided in `CITATION.cff`. Add the final publication DOI and repository DOI when they become available.

## License

No software license has been selected yet. Until a license file is added, normal copyright restrictions apply.
