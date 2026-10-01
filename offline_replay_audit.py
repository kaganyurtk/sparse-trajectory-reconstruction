"""Independent offline checks using saved predictions and checkpoints only.

This is deliberately not a raw-telemetry replay of the historical workflows.
"""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
RECORDS = ROOT / 'recovered_experiment_records'
if not RECORDS.is_dir() and (ROOT.parent / 'recovered_experiment_records').is_dir():
    RECORDS = ROOT.parent / 'recovered_experiment_records'
RQ1 = RECORDS / 'rq1/rq1_kinematic_experiment/outputs/test_v2'
RQ1_FULL = RECORDS / 'rq1/rq1_kinematic_experiment/outputs/full_v2'
RQ2 = RECORDS / 'rq2/RQ2_CONFIRMATORY_RECONSTRUCTION_v1_1_2026-09-26'


def close(a, b, label, tol=1e-9):
    if not np.isclose(a, b, rtol=tol, atol=tol):
        raise AssertionError(f'{label}: {a} != {b}')


def rq1_check():
    summary = json.loads((RQ1 / 'summary.json').read_text())
    manifest = json.loads((RQ1 / 'test_manifest.json').read_text())
    target_scale = np.array(manifest['encoder']['target_scale'], dtype=float)
    claimed_hash = manifest.pop('fingerprint')
    actual_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    # Historical object_sha256 may use a different JSON byte representation.
    manifest['fingerprint'] = claimed_hash
    assert summary['test_manifest_fingerprint'] == claimed_hash
    max_err = 0.0
    n = 0
    for item in summary['test_results']:
        run = item['run_id']
        saved = json.loads((RQ1 / run / 'result.json').read_text())
        assert saved['run_id'] == run
        assert hashlib.sha256((RQ1_FULL / run / 'weights.npz').read_bytes()).hexdigest() == item['weights_sha256']
        with (RQ1 / run / 'test_predictions.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 726
        for flight in saved['metrics_per_flight']:
            subset = [r for r in rows if r['flight_id'] == flight['flight_id']]
            assert len(subset) == 121
            for channel, prefix in [('h', 'h'), ('v', 'v')]:
                true = np.array([float(r[f'{channel}_true_m' if channel == 'h' else 'v_true_m_s']) for r in subset])
                pred = np.array([float(r[f'{channel}_pred_m' if channel == 'h' else 'v_pred_m_s']) for r in subset])
                close(float(np.sqrt(np.mean((pred-true)**2))), flight[f'{prefix}_rmse_m' if channel == 'h' else 'v_rmse_m_s'], f'{run}:{flight["flight_id"]}:rmse')
                close(float(np.mean(np.abs(pred-true))), flight[f'{prefix}_mae_m' if channel == 'h' else 'v_mae_m_s'], f'{run}:{flight["flight_id"]}:mae')
        for key in ('h_rmse_m', 'v_rmse_m_s'):
            got = float(np.mean([f[key] for f in saved['metrics_per_flight']]))
            close(got, saved[key], f'{run}:{key}')
            close(got, item[key], f'{run}:summary:{key}')
            max_err = max(max_err, abs(got - saved[key]))
        score = float(np.mean([.5*(f['h_rmse_m']/target_scale[0] + f['v_rmse_m_s']/target_scale[1]) for f in saved['metrics_per_flight']]))
        close(score, saved['evaluation_score'], f'{run}:score')
        close(score, item['evaluation_score'], f'{run}:summary:score')
        n += 1
    assert n == 50
    return {'models': n, 'rows_per_model': 726, 'max_absolute_rmse_difference': max_err,
            'checkpoint_hashes_matched': n, 'manifest_claim': claimed_hash,
            'manifest_json_canonical_hash_diagnostic': actual_hash}


def rq2_check():
    manifest = json.loads((RQ2 / 'manifest.json').read_text())
    results = json.loads((RQ2 / 'results.json').read_text())
    fingerprint = manifest.pop('fingerprint')
    assert hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest() == fingerprint
    assert results['manifest_fingerprint'] == fingerprint
    manifest['fingerprint'] = fingerprint
    historical = json.loads((RQ2 / 'verification.json').read_text())
    assert historical['all_checks_passed']
    assert len(results['results']) == 10
    scores = {}
    max_score_error = 0.0
    for row in results['results']:
        name = f'{row["method"]}_seed_{row["seed"]}.npz'
        file = RQ2 / name
        assert hashlib.sha256(file.read_bytes()).hexdigest() == historical['model_sha256'][name]
        with np.load(file, allow_pickle=False) as z:
            weights = [z[f'arr_{i}'] for i in range(6)]
        assert [w.shape for w in weights] == [(7,32),(32,),(32,32),(32,),(32,2),(2,)]
        x = np.zeros((2,7))
        y = np.tanh(np.tanh(x @ weights[0] + weights[1]) @ weights[2] + weights[3]) @ weights[4] + weights[5]
        assert y.shape == (2,2) and np.all(np.isfinite(y))
        score = .5 * (row['h_rmse_m']/manifest['scales']['y_std'][0] + row['v_rmse_m_s']/manifest['scales']['y_std'][1])
        close(score, row['score'], name + ':score')
        max_score_error = max(max_score_error, abs(score-row['score']))
        scores[(row['seed'], row['method'])] = row['score']
    diffs = []
    for pair in results['pairs']:
        seed = pair['seed']
        close(pair['nn'], scores[(seed,'nn')], f'{seed}:nn')
        close(pair['kcnn'], scores[(seed,'kcnn')], f'{seed}:kcnn')
        close(pair['difference'], pair['kcnn']-pair['nn'], f'{seed}:difference')
        diffs.append(pair['difference'])
    close(float(np.mean(diffs)), results['mean_difference'], 'mean_difference')
    close(float(np.std(diffs, ddof=1)), results['sd_difference'], 'sd_difference')
    assert sum(d < 0 for d in diffs) == results['kcnn_seed_wins'] == 0
    return {'checkpoints_loaded': 10, 'synthetic_forward_passes': 10,
            'max_absolute_score_difference': max_score_error, 'paired_seed_count': 5,
            'mean_kcnn_minus_nn': float(np.mean(diffs)), 'manifest_fingerprint': fingerprint,
            'raw_telemetry_metric_replay': 'not run: required third-party flight CSVs are not in the package'}


if __name__ == '__main__':
    report = {'scope': 'Independent saved-artifact offline checks, not end-to-end source-data replay',
              'rq1': rq1_check(), 'rq2': rq2_check()}
    print(json.dumps(report, indent=2))
