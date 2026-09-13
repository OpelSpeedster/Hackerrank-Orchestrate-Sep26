from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source"
CODE_DIR = ROOT / "code"
for import_path in (SOURCE_DIR, CODE_DIR, ROOT):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from validation import write_output  # noqa: E402

from gateway import GroqGateway  # noqa: E402
from ingestion import load_all  # noqa: E402
from metrics import PipelineMetrics  # noqa: E402
from modal_client import ModalClient  # noqa: E402
from orchestrator import ElasticRouter  # noqa: E402
from retrieval import EvidenceIndex  # noqa: E402
from tools import FinancialTools  # noqa: E402


def _load_environment(root: Path) -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
    except ImportError:
        pass


async def run_pipeline(root: Path, output_path: Path, disable_models: bool = False) -> int:
    ingested = load_all(root / "dataset")
    dataset = ingested.dataset
    metrics = PipelineMetrics(
        extraction_model=os.getenv("EXTRACTION_MODEL", "qwen/qwen3.8-27b"),
        guard_model=os.getenv(
            "REASONING_MODEL", "meta-llama/llama-prompt-guard-2-86m"
        ),
    )
    models_enabled = not disable_models and os.getenv("GROQ_ENABLE_AGENT", "1").lower() not in {
        "0", "false", "no"
    }
    gateway = GroqGateway(metrics, enabled_override=models_enabled)
    modal = ModalClient(float(os.getenv("MODAL_TIMEOUT_SECONDS", "30")))
    index = EvidenceIndex(dataset)
    tools = FinancialTools(root / "dataset", dataset, index, gateway, modal)
    router = ElasticRouter(tools, metrics)

    if gateway.enabled:
        print(
            f"Groq agent enabled: Qwen={gateway.extraction_model}, "
            f"Meta={gateway.guard_model}"
        )
    else:
        print("Groq agent unavailable; using deterministic tools and fallbacks.")
    if modal.enabled:
        print("Modal document/embedding adapter enabled.")
    else:
        print("Modal adapter not configured; local retrieval and deterministic fallbacks enabled.")

    results: list[dict | None] = [None] * len(dataset.requests)

    async def process(index_value: int, request):
        return index_value, await router.process(request)

    tasks = [
        asyncio.create_task(process(index_value, request))
        for index_value, request in enumerate(dataset.requests)
    ]
    completed = 0
    for future in asyncio.as_completed(tasks):
        index_value, result = await future
        results[index_value] = result
        completed += 1
        print(f"\rProcessed {completed}/{len(tasks)} requests", end="", flush=True)
    print()

    rows = [result["row"] for result in results if result is not None]
    if len(rows) != len(dataset.requests):
        raise RuntimeError(f"Expected {len(dataset.requests)} rows, got {len(rows)}")
    write_output(output_path, rows)
    metrics.write_reports(root, output_path)
    print(f"Wrote {len(rows)} rows to {output_path}")
    print(f"Usage report: {root / 'evaluation' / 'usage_report.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Buy or Wait? agent pipeline.")
    parser.add_argument("--dataset", default="dataset", help="Dataset directory relative to the repository root.")
    parser.add_argument("--output", default="output.csv", help="Output CSV path relative to the repository root.")
    parser.add_argument("--no-models", action="store_true", help="Disable Groq and Modal model calls.")
    args = parser.parse_args(argv)
    root = ROOT
    _load_environment(root)
    dataset_path = (root / args.dataset).resolve()
    output_path = (root / args.output).resolve()
    return asyncio.run(run_pipeline(root, output_path, args.no_models))


if __name__ == "__main__":
    raise SystemExit(main())
