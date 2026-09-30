# Sparse Rocket Trajectory Reconstruction

This directory contains the main RQ1 Falcon 9 experiment code for *When kinematic constraints conflict with rocket telemetry: sparse trajectory reconstruction across two real-flight datasets*. RQ2 preparation utilities are located in the repository's sibling `rq2/` directory.

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
- `../rq2/`: FlightSketch curation, identity-review, deterministic split preparation, and gate-verification utilities.

Generated predictions, model weights, processed telemetry, and other bulky run artifacts are intentionally excluded from this code package.

## Relationship between RQ1 and RQ2

RQ2 does not introduce a third model architecture. It carries the same matched NN and KC-NN model family and comparison logic developed for RQ1 into an independent public-source reconstruction setting. The RQ2 analysis nevertheless uses its own FlightSketch fit/validation partitions, fit-only target scaling, deterministic sparse-observation masks, and paired optimization seeds. It is therefore a cross-dataset application of the same method, not a zero-shot evaluation of frozen Falcon 9 weight files.

The `rq2/` directory contains the shareable FlightSketch source-audit, identity-review, and split-gate utilities recovered from the frozen Drive package. It intentionally excludes raw or processed third-party trajectories, trained checkpoints, and generated result trees. The historical RQ2 model-fitting/evaluation runner was not present in the recovered shareable archive, so this repository does not claim that the RQ2 numerical results can be reproduced end to end from the included files alone.

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

For RQ1, this release provides the complete experiment code but not the processed telemetry or trained weights. For RQ2, it provides the recovered shareable curation and split-preparation code but not the historical model-fitting/evaluation runner, processed trajectories, checkpoints, or generated result tree. Consequently, source-level and synthetic checks can be inspected immediately, while end-to-end numerical reproduction requires the missing frozen artifacts and authorized data access. The study covers sparse trajectory reconstruction and should not be interpreted as full-flight or orbital prediction.

## Citation

Citation metadata is provided in `CITATION.cff`. Add the final publication DOI and repository DOI when they become available.

## License

Code is covered by the repository-root MIT License. Author-written prose is covered by CC BY 4.0. See `../LICENSE_SCOPE.md`; third-party telemetry is excluded.
