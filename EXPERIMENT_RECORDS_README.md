# Recovered experiment records

This archive restores the original RQ1 final, NEXT-5 ablation, Iridium-family and RQ2 reconstruction v1.1 packages. Original file contents and historical verification records are preserved. See RECOVERED_RECORDS_VERIFICATION.json beside this archive for the new integrity checks.

The rq1 directory contains the final run/test manifests, inner split, model outputs and verification records. The ablation and iridium directories contain their original runners and output records. The rq2 directory contains the final flight split, fingerprinted manifest, ten saved checkpoints, results, source-snapshot verification and independent replay script.

RQ2 v1.1 fitted NN and KC-NN on FlightSketch fitting groups. It did not directly load Falcon 9 RQ1 checkpoint weights. Its 32-by-32 tanh architecture and experimental comparison belong to the same study framework; fitted weights are dataset-specific.

Original scripts retain historical workspace paths so source hashes remain meaningful. Running them requires configuring those paths and supplying the permitted input telemetry, identity workbook and candidate manifest. Do not run a training script merely to inspect the archive. The original RQ2 report documents why v1.1 is a confirmatory reconstruction rather than a pristine sealed historical test.

The historical replay reports are not new replay results. This recovery checked archive hashes, ten RQ2 checkpoint hashes, the RQ2 manifest fingerprint, test IDs, group separation and the RQ1 inner split. Raw telemetry is not supplied by this recovery.
