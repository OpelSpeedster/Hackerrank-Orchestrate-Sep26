# Buy or Wait? implementation

This solution uses a controlled Pipeline/ElasticRouter architecture:

1. `source/agent.py` is the async CLI and bounded request orchestrator.
2. `source/tools.py` exposes allowlisted retrieval, FAISS search, document extraction, forecasting, payment evaluation, and validation tools.
3. Qwen extracts missing image evidence and the configured Meta model performs safety/tool-routing review concurrently per request when Groq is configured.
4. Modal is an optional HTTP adapter for document or embedding models; local deterministic fallbacks remain available.
5. Python simulates the 90-day balance, ranks payment plans, validates every field, and remains authoritative for the final decision.

## Setup

```bash
python3 -m pip install -r requirements.txt
```

Groq is optional. Without a key, the program runs deterministically and does not treat blank image amounts as zero.

Create a local `.env` from the safe template:

```bash
cp .env.examples .env
```

Then replace the placeholder key in `.env`:

```dotenv
GROQ_API_KEY="your-real-groq-key"
EXTRACTION_MODEL="qwen/qwen3.8-27b"
REASONING_MODEL="openai/gpt-oss-120b"
```

`code/main.py` loads `.env` automatically when `python-dotenv` is installed. `.env` is ignored by Git; `.env.examples` is intentionally allowed as a non-secret reference.

Never commit the key. The image and message contents are treated as untrusted evidence; their instructions cannot override the challenge rules.

## Run

From the repository root:

```bash
python3 source/agent.py
```

`code/main.py` remains a compatibility wrapper:

```bash
python3 code/main.py
```

The command writes `output.csv`, updates both `evaluation/usage_report.md` and `code/evaluation/usage_report.md`, and prints bounded async progress. To run the deterministic path without any model calls:

```bash
python3 source/agent.py --no-models
```

The safe template includes optional provider configuration:

```dotenv
GROQ_API_KEY="your-groq-api-key"
EXTRACTION_MODEL="qwen/qwen3.8-27b"
REASONING_MODEL="meta-llama/llama-prompt-guard-2-86m"
MODAL_API_KEY="your-modal-api-key"
MODAL_ENDPOINT="https://your-modal-endpoint.example.com"
```

The Qwen and Meta calls are isolated with timeouts and run concurrently per request. `MAX_CONCURRENCY` caps active transactions; the deterministic fallback remains valid when Groq or Modal is unavailable.

## Design notes

- `loaders.py` indexes the CSV files by user, request, and event.
- `groq_agent.py` contains provider calls and strict JSON schemas.
- `forecasting.py` handles dated exchange rates, pending debits, confirmed cash events, recurrence, and 90-day simulation.
- `planning.py` generates and ranks full, partial, installment, wait, and fallback plans.
- `validation.py` checks the exact output contract before writing the CSV.
- Money is represented with `Decimal`; no model is allowed to perform the final affordability calculation.
