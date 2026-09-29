# Iridium-family leave-one-flight-out replication report

## Outcome

The locked family-level decision rule **failed**. The upper-bound-only model beat NN on
2/5 held-out Iridium flights; at least 4/5 were required. Its five-flight mean
difference was -0.0061, which was negative only because the gains on NEXT-4
and NEXT-8 were larger than the losses on the other three flights. This does not support a
family-wide Iridium effect.

| Held-out flight | NN | Full KC-NN | Upper-bound only | Upper minus NN | Favored |
|---|---:|---:|---:|---:|---|
| NEXT-1 | 0.0960 | 0.1251 | 0.1129 | +0.0169 | NN |
| NEXT-3 | 0.1740 | 0.2120 | 0.2111 | +0.0371 | NN |
| NEXT-4 | 0.2654 | 0.2194 | 0.2080 | -0.0573 | Upper |
| NEXT-6 | 0.1180 | 0.1455 | 0.1326 | +0.0146 | NN |
| NEXT-8 | 0.2169 | 0.1818 | 0.1753 | -0.0416 | Upper |

Across the five held-out flights, the unweighted mean composite errors were
0.1741 (NN), 0.1768 (full KC-NN), and
0.1680 (upper-bound only). The upper-bound-only mean is lowest,
but the benefit is not flight-consistent and therefore does not pass the prespecified rule.

## Seed consistency

Upper-bound only beat NN for all five seeds on NEXT-4 and NEXT-8, for one of five seeds on
NEXT-1, and for zero of five seeds on NEXT-3 and NEXT-6. The heterogeneous flight result is
therefore not caused by a single initialization.

## Mechanistic interpretation

The model inputs cannot uniquely identify an Iridium trajectory. NEXT-1 and NEXT-4 have the
same model-visible static inputs (Block 3 and 9,600 kg payload), yet their true trajectories
differ by 731.3 m altitude RMSE and 42.09 m/s speed RMSE over 0–120 s. Mission
identity, orbit details, landing mode, and other flight-specific state are not supplied to the
network. A shared physical regularizer can move the prediction toward one member of such an
input-equivalent pair while moving it away from another.

## Scientific conclusion

The earlier Iridium NEXT-5 benefit remains a valid flight-level mechanism observation, but it
does not generalize to the Iridium family under the locked 4/5 criterion. The defensible RQ1
conclusion remains that physics constraints provide heterogeneous, locally aligned benefits
rather than a uniform accuracy improvement. This replication is post-hoc relative to RQ1 and
must not be presented as part of the preregistered primary analysis.
