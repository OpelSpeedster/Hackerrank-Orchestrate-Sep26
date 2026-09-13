from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
CODE = ROOT / "code"
for path in (SOURCE, CODE, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from gateway import GroqGateway  # noqa: E402
from ingestion import load_all  # noqa: E402
from metrics import PipelineMetrics  # noqa: E402
from modal_client import ModalClient  # noqa: E402
from orchestrator import ElasticRouter  # noqa: E402
from planning import plan_request  # noqa: E402
from retrieval import EvidenceIndex  # noqa: E402
from tools import FinancialTools  # noqa: E402
from validation import validate_row  # noqa: E402


def load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def run(args: argparse.Namespace) -> int:
    load_environment()
    ingested = load_all(ROOT / "dataset")
    dataset = ingested.dataset
    requests = {request.request_id: request for request in dataset.requests}
    cases = load_cases(ROOT / "benchmarks" / "cases.jsonl")[: args.limit or None]
    metrics = PipelineMetrics(
        extraction_model=os.getenv("EXTRACTION_MODEL", "qwen/qwen3.8-27b"),
        guard_model=os.getenv("ORCHESTRATOR_MODEL", os.getenv("REASONING_MODEL", "gpt-5.6-luna")),
        modal_model=os.getenv("EMBEDDING_MODEL", ""),
    )
    models_enabled = not args.no_models and os.getenv("GROQ_ENABLE_AGENT", "1").lower() not in {"0", "false", "no"}
    gateway = GroqGateway(metrics, enabled_override=models_enabled)
    modal = ModalClient(
        float(os.getenv("MODAL_TIMEOUT_SECONDS", "30")),
        metrics,
        enabled_override=not args.no_models,
    )
    index = EvidenceIndex(dataset)
    if os.getenv("EMBEDDING_PROVIDER", "local").lower() == "modal" and modal.enabled:
        await index.build_remote_embeddings(modal)
    tools = FinancialTools(ROOT / "dataset", dataset, index, gateway, modal)
    router = ElasticRouter(tools, metrics)

    results = []
    for case in cases:
        request_id = case["request_id"]
        request = requests.get(request_id)
        if request is None:
            results.append({"case_id": case["case_id"], "request_id": request_id, "status": "missing_request"})
            continue
        baseline, _ = plan_request(dataset, request)
        started = time.perf_counter()
        result = await router.process(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        row = result["row"]
        errors = validate_row(dataset, request, row)
        core_fields = (
            "amount_safe_to_pay",
            "affordability_status",
            "recommended_payment_method",
            "payment_plan",
            "earliest_date_for_full_payment",
            "spending_changes_needed",
        )
        agreement = all(row.get(field) == baseline.get(field) for field in core_fields)
        results.append(
            {
                "case_id": case["case_id"],
                "request_id": request_id,
                "focus": case.get("focus", ""),
                "status": "passed" if not errors else "failed_validation",
                "validation_errors": errors,
                "deterministic_core_agreement": agreement,
                "latency_ms": round(elapsed_ms, 2),
                "trace": result.get("trace", []),
                "provider_errors": result.get("errors", []),
                "guard_status": (result.get("guard") or {}).get("status", "disabled"),
            }
        )

    passed = sum(item.get("status") == "passed" for item in results)
    agreement = sum(bool(item.get("deterministic_core_agreement")) for item in results if "deterministic_core_agreement" in item)
    latencies = [item["latency_ms"] for item in results if "latency_ms" in item]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cases": len(results),
        "passed_validation": passed,
        "validation_pass_rate": passed / len(results) if results else 0,
        "deterministic_core_agreement_count": agreement,
        "deterministic_core_agreement_rate": agreement / len(latencies) if latencies else 0,
        "average_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "models": {
            "provider": "Groq + OpenAI-compatible orchestrator + Modal",
            "extraction": metrics.extraction_model,
            "orchestrator": metrics.guard_model,
            "embedding": metrics.modal_model,
        },
        "results": results,
    }
    results_dir = ROOT / "benchmarks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "latest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown = [
        "# Agent Benchmark",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"- Cases: {summary['cases']}",
        f"- Validation pass rate: {summary['validation_pass_rate']:.2%}",
        f"- Deterministic core agreement rate: {summary['deterministic_core_agreement_rate']:.2%}",
        f"- Average latency (ms): {summary['average_latency_ms']:.2f}",
        f"- Orchestrator model: `{metrics.guard_model}`",
        "",
        "| case_id | request_id | status | validation_errors | core_agreement | latency_ms | guard_status | provider_errors |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for item in results:
        markdown.append(
            f"| {item['case_id']} | {item['request_id']} | {item['status']} | "
            f"{', '.join(item.get('validation_errors', []))} | "
            f"{item.get('deterministic_core_agreement', '')} | {item.get('latency_ms', '')} | "
            f"{item.get('guard_status', '')} | {', '.join(item.get('provider_errors', []))} |"
        )
    (results_dir / "latest.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"Benchmark cases: {len(results)}")
    print(f"Validation pass rate: {summary['validation_pass_rate']:.2%}")
    print(f"Results: {results_dir / 'latest.md'}")
    return 0 if passed == len(results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the agent without modifying output.csv.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-models", action="store_true")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
