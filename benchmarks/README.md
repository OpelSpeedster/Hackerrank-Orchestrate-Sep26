# Agent benchmark

This benchmark follows the workflow in the repository `README.md`: inspect solved samples, reconstruct evidence, forecast and plan deterministically, validate the structured decision, score labeled samples, and then validate the full unlabeled request set. It evaluates the financial orchestrator only; it does not benchmark the coding agent.

Run the fixed benchmark cases without changing `output.csv`:

```bash
python3 benchmarks/run.py --no-models
```

With configured providers:

```bash
python3 benchmarks/run.py
```

The benchmark uses the provider selected by `ORCHESTRATOR_PROVIDER` and `ORCHESTRATOR_MODEL`. It never uses benchmark results as labels for the official evaluation output.

Results are written to:

```text
benchmarks/results/latest.json
benchmarks/results/latest.md
```

The benchmark measures validation pass rate, agreement with the deterministic financial core, latency, provider status, and tool traces. It is a regression/safety benchmark; it does not replace the official full-dataset evaluator. The full evaluator is run with:

```bash
python3 code/evaluation/main.py
```

Because `dataset/requests.csv` has no visible answer labels, full-dataset evaluation reports contract and safety correctness rather than hidden-label accuracy.

Deploy the embedding service with:

```bash
modal deploy source/modal_app.py
```

Set the callable `.modal.run` URL printed by the deployment as `MODAL_ENDPOINT`; the Modal dashboard URL is not an inference endpoint. Smoke-test it without running the full benchmark:

```bash
python3 benchmarks/modal_smoke.py --endpoint "$MODAL_ENDPOINT"
```

The normal benchmark uses deterministic/local retrieval unless Modal is explicitly enabled, keeping benchmark latency bounded.

## Sample-request orchestrator benchmark

Run only the 25 labeled examples in `dataset/sample_requests.csv`:

```bash
python3 benchmarks/run_sample_orchestrator.py
```

Run the deterministic comparison separately:

```bash
python3 benchmarks/run_sample_orchestrator.py --no-models
```

These runs write:

```text
benchmarks/results/sample_orchestrator_model.json
benchmarks/results/sample_orchestrator_model.md
benchmarks/results/sample_orchestrator_deterministic.json
benchmarks/results/sample_orchestrator_deterministic.md
```

The sample CSV labels are treated as benchmark labels for this focused test. The model is scored on routing/provider behavior and agreement with those labels, but it cannot override the deterministic financial planner or validator. A valid schema is not the same as an accurate decision; review accuracy, precision/recall, provider failures, fallback rate, safety validation, and latency together.
