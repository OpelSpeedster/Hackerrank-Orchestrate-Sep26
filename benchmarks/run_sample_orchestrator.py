from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
from models import Request, decimal  # noqa: E402
from orchestrator import ElasticRouter  # noqa: E402
from retrieval import EvidenceIndex  # noqa: E402
from tools import FinancialTools  # noqa: E402
from validation import validate_row  # noqa: E402

STRUCTURED_FIELDS = (
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
)
CLASS_FIELDS = ("affordability_status", "recommended_payment_method")
ALLOWED_ROUTER_TOOLS = {
    "search_faiss",
    "extract_document",
    "forecast_balance",
    "evaluate_payment_options",
    "validate_decision",
}


def load_environment() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def parse_sample_requests(path: Path) -> tuple[list[Request], dict[str, dict[str, str]]]:
    requests: list[Request] = []
    gold: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            request = Request(
                request_id=row["request_id"],
                user_id=row["user_id"],
                request_date=row["request_date"],
                request_type=row["request_type"],
                requested_amount=decimal(row["requested_amount"]),
                desired_completion_date=row["desired_completion_date"],
                allows_partial_payment=row["allows_partial_payment"].strip().lower() == "true",
                request_text=row["request_text"],
            )
            requests.append(request)
            gold[request.request_id] = row
    return requests, gold


def amount(value: str | None) -> Decimal | None:
    try:
        return Decimal(str(value).strip()) if value is not None and str(value).strip() else None
    except (InvalidOperation, ValueError):
        return None


def exact_amount(left: str | None, right: str | None) -> bool:
    return amount(left) == amount(right)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * fraction)))
    return ordered[index]


def classification_scores(
    pairs: list[tuple[str, str]], labels: set[str]
) -> dict[str, object]:
    confusion = {label: {other: 0 for other in sorted(labels)} for label in sorted(labels)}
    for expected, predicted in pairs:
        confusion.setdefault(expected, {}).setdefault(predicted, 0)
        confusion[expected][predicted] += 1
    per_class: dict[str, dict[str, float]] = {}
    for label in sorted(labels):
        tp = confusion.get(label, {}).get(label, 0)
        fp = sum(confusion.get(other, {}).get(label, 0) for other in labels if other != label)
        fn = sum(confusion.get(label, {}).get(other, 0) for other in labels if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(confusion.get(label, {}).values()),
        }
    macro = {
        name: sum(metrics[name] for metrics in per_class.values()) / len(per_class)
        if per_class else 0.0
        for name in ("precision", "recall", "f1")
    }
    return {"confusion_matrix": confusion, "per_class": per_class, "macro": macro}


def provider_names() -> str:
    names = ["Groq"]
    provider = os.getenv("ORCHESTRATOR_PROVIDER", "groq").lower()
    if provider not in {"", "groq"}:
        names.append(provider.title())
    if os.getenv("MODAL_ENDPOINT", "").strip():
        names.append("Modal")
    return " + ".join(names)


async def run(args: argparse.Namespace) -> int:
    load_environment()
    ingested = load_all(ROOT / "dataset")
    dataset = ingested.dataset
    sample_requests, gold = parse_sample_requests(ROOT / "dataset" / "sample_requests.csv")
    missing_users = sorted({request.user_id for request in sample_requests} - set(dataset.profiles))
    if missing_users:
        raise RuntimeError(f"Sample users missing from financial_profiles.csv: {missing_users}")
    dataset.requests = sample_requests

    metrics = PipelineMetrics(
        extraction_model=os.getenv("EXTRACTION_MODEL", "qwen/qwen3.8-27b"),
        guard_model=os.getenv("ORCHESTRATOR_MODEL", os.getenv("REASONING_MODEL", "gpt-5.6-luna")),
        modal_model=os.getenv("EMBEDDING_MODEL", ""),
        provider=provider_names(),
    )
    models_enabled = not args.no_models and os.getenv("GROQ_ENABLE_AGENT", "1").lower() not in {"0", "false", "no"}
    gateway = GroqGateway(metrics, enabled_override=models_enabled)
    modal = ModalClient(
        float(os.getenv("MODAL_TIMEOUT_SECONDS", "30")),
        metrics,
        enabled_override=not args.no_models,
    )
    index = EvidenceIndex(dataset)
    tools = FinancialTools(ROOT / "dataset", dataset, index, gateway, modal)
    router = ElasticRouter(tools, metrics)

    results: list[dict[str, object]] = []
    status_pairs: list[tuple[str, str]] = []
    method_pairs: list[tuple[str, str]] = []
    amount_errors: list[float] = []
    for request in sample_requests:
        expected = gold[request.request_id]
        started = time.perf_counter()
        result = await router.process(request)
        latency_ms = (time.perf_counter() - started) * 1000
        row = result.get("row", {})
        validation_errors = validate_row(dataset, request, row)
        status_pairs.append((expected["affordability_status"], str(row.get("affordability_status", ""))))
        method_pairs.append((expected["recommended_payment_method"], str(row.get("recommended_payment_method", ""))))
        expected_amount = amount(expected.get("amount_safe_to_pay"))
        predicted_amount = amount(row.get("amount_safe_to_pay"))
        amount_error = float(abs(expected_amount - predicted_amount)) if expected_amount is not None and predicted_amount is not None else None
        if amount_error is not None:
            amount_errors.append(amount_error)
        field_matches = {
            field: (exact_amount(row.get(field), expected.get(field)) if field == "amount_safe_to_pay" else row.get(field) == expected.get(field))
            for field in STRUCTURED_FIELDS
        }
        guard = result.get("guard") or {}
        requested_tools = guard.get("requested_tools", []) if isinstance(guard, dict) else []
        invalid_tools = guard.get("rejected_tools", []) if isinstance(guard, dict) else []
        results.append(
            {
                "request_id": request.request_id,
                "latency_ms": round(latency_ms, 3),
                "validation_errors": validation_errors,
                "valid_contract": not validation_errors,
                "fallback_used": bool(metrics.request_metrics[-1].fallback_used) if metrics.request_metrics else True,
                "structured_field_matches": field_matches,
                "structured_decision_exact": all(field_matches.values()),
                "amount_absolute_error": amount_error,
                "expected_affordability_status": expected["affordability_status"],
                "predicted_affordability_status": row.get("affordability_status", ""),
                "expected_payment_method": expected["recommended_payment_method"],
                "predicted_payment_method": row.get("recommended_payment_method", ""),
                "expected_payment_plan": expected["payment_plan"],
                "predicted_payment_plan": row.get("payment_plan", ""),
                "orchestrator_status": guard.get("status", "disabled") if isinstance(guard, dict) else "disabled",
                "orchestrator_flagged": bool(guard.get("flagged")) if isinstance(guard, dict) else False,
                "requested_tools": requested_tools,
                "invalid_requested_tools": invalid_tools,
                "rejected_requested_tools": invalid_tools,
                "provider_errors": result.get("errors", []),
                "trace": result.get("trace", []),
            }
        )

    latencies = [float(item["latency_ms"]) for item in results]
    exact_count = sum(bool(item["structured_decision_exact"]) for item in results)
    valid_count = sum(bool(item["valid_contract"]) for item in results)
    fallback_count = sum(bool(item["fallback_used"]) for item in results)
    plan_exact_count = sum(
        bool(item["structured_field_matches"].get("payment_plan")) for item in results
    )
    invalid_tool_count = sum(len(item["invalid_requested_tools"]) for item in results)
    status_metrics = classification_scores(status_pairs, {item[0] for item in status_pairs} | {item[1] for item in status_pairs})
    method_metrics = classification_scores(method_pairs, {item[0] for item in method_pairs} | {item[1] for item in method_pairs})
    mode = "model" if models_enabled else "deterministic"
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "dataset/sample_requests.csv only",
        "label_source": "completed labels in dataset/sample_requests.csv",
        "sample_count": len(results),
        "output_csv_modified": False,
        "model_outputs_non_authoritative": True,
        "mode": mode,
        "models_enabled": models_enabled,
        "provider": metrics.provider,
        "orchestrator_model": metrics.guard_model,
        "extraction_model": metrics.extraction_model,
        "metrics": {
            "structured_decision_accuracy": exact_count / len(results) if results else 0.0,
            "status_accuracy": sum(expected == predicted for expected, predicted in status_pairs) / len(status_pairs) if status_pairs else 0.0,
            "payment_method_accuracy": sum(expected == predicted for expected, predicted in method_pairs) / len(method_pairs) if method_pairs else 0.0,
            "status": status_metrics,
            "payment_method": method_metrics,
            "payment_plan_exact_match_rate": plan_exact_count / len(results) if results else 0.0,
            "amount_mae": statistics.mean(amount_errors) if amount_errors else None,
            "amount_median_absolute_error": statistics.median(amount_errors) if amount_errors else None,
            "validation_pass_rate": valid_count / len(results) if results else 0.0,
            "fallback_rate": fallback_count / len(results) if results else 0.0,
            "invalid_requested_tool_count": invalid_tool_count,
            "average_latency_ms": statistics.mean(latencies) if latencies else 0.0,
            "p50_latency_ms": percentile(latencies, 0.50),
            "p95_latency_ms": percentile(latencies, 0.95),
            "p99_latency_ms": percentile(latencies, 0.99),
            "min_latency_ms": min(latencies) if latencies else 0.0,
            "max_latency_ms": max(latencies) if latencies else 0.0,
        },
        "provider_usage": {
            "groq_orchestrator_and_extraction_calls": metrics.model_calls,
            "successful_groq_calls": metrics.successful_model_calls,
            "modal_calls": metrics.modal_calls,
            "successful_modal_calls": metrics.modal_successes,
            "total_provider_calls": metrics.model_calls + metrics.modal_calls,
            "failed_calls": metrics.failed_calls,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "estimated_cost_usd": str(metrics.estimated_cost_usd),
            "error_counts": metrics.error_counts,
            "orchestrator_completed": metrics.guard_completed,
            "orchestrator_failed": metrics.guard_failed,
            "orchestrator_timeouts": metrics.guard_timed_out,
            "orchestrator_invalid_responses": metrics.guard_invalid_response,
        },
        "results": results,
    }

    results_dir = ROOT / "benchmarks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_json = results_dir / f"sample_orchestrator_{mode}.json"
    report_md = results_dir / f"sample_orchestrator_{mode}.md"
    (report_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (results_dir / "sample_orchestrator_latest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    status_macro = status_metrics["macro"]
    method_macro = method_metrics["macro"]
    markdown = [
        "# Sample-request orchestrator benchmark",
        "",
        "This report evaluates only `dataset/sample_requests.csv`; it does not benchmark the coding agent and does not modify `output.csv`.",
        "Model outputs are non-authoritative: deterministic Python forecasting, planning, and validation produce the final structured decision.",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Sample requests: {len(results)}",
        f"- Labels: completed fields in `dataset/sample_requests.csv`",
        f"- Models enabled: `{models_enabled}`",
        f"- Provider/model: `{metrics.provider}` / `{metrics.guard_model}`",
        "",
        "## Summary",
        "",
        f"- Structured decision accuracy: **{summary['metrics']['structured_decision_accuracy']:.2%}**",
        f"- Affordability-status accuracy: **{summary['metrics']['status_accuracy']:.2%}**",
        f"- Payment-method accuracy: **{summary['metrics']['payment_method_accuracy']:.2%}**",
        f"- Status macro precision / recall / F1: **{status_macro['precision']:.2%} / {status_macro['recall']:.2%} / {status_macro['f1']:.2%}**",
        f"- Method macro precision / recall / F1: **{method_macro['precision']:.2%} / {method_macro['recall']:.2%} / {method_macro['f1']:.2%}**",
        f"- Payment-plan exact match: **{summary['metrics']['payment_plan_exact_match_rate']:.2%}**",
        f"- Safe-amount MAE: **{summary['metrics']['amount_mae']}**",
        f"- Contract validation pass rate: **{summary['metrics']['validation_pass_rate']:.2%}**",
        f"- Fallback rate: **{summary['metrics']['fallback_rate']:.2%}**",
        f"- Average / P50 / P95 / P99 latency (ms): **{summary['metrics']['average_latency_ms']:.2f} / {summary['metrics']['p50_latency_ms']:.2f} / {summary['metrics']['p95_latency_ms']:.2f} / {summary['metrics']['p99_latency_ms']:.2f}**",
        f"- Invalid requested tools: **{summary['metrics']['invalid_requested_tool_count']}**",
        "",
        "## Confusion matrices",
        "",
        "### Affordability status",
        "",
        "```json",
        json.dumps(status_metrics["confusion_matrix"], indent=2),
        "```",
        "",
        "### Payment method",
        "",
        "```json",
        json.dumps(method_metrics["confusion_matrix"], indent=2),
        "```",
        "",
        "## Per-request results",
        "",
        "| request_id | exact | valid | expected_status | predicted_status | expected_method | predicted_method | amount_abs_error | latency_ms | orchestrator_status | fallback | errors |",
        "|---|---:|---:|---|---|---|---|---:|---:|---|---:|---|",
    ]
    for item in results:
        markdown.append(
            f"| {item['request_id']} | {item['structured_decision_exact']} | {item['valid_contract']} | "
            f"{item['expected_affordability_status']} | {item['predicted_affordability_status']} | "
            f"{item['expected_payment_method']} | {item['predicted_payment_method']} | "
            f"{item['amount_absolute_error']} | {item['latency_ms']} | {item['orchestrator_status']} | "
            f"{item['fallback_used']} | {', '.join(item['provider_errors'])} |"
        )
    report_md.write_text("\n".join(markdown) + "\n", encoding="utf-8")
    (results_dir / "sample_orchestrator_latest.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"Sample orchestrator cases: {len(results)}")
    print(f"Structured decision accuracy: {summary['metrics']['structured_decision_accuracy']:.2%}")
    print(f"Validation pass rate: {summary['metrics']['validation_pass_rate']:.2%}")
    print(f"Average latency: {summary['metrics']['average_latency_ms']:.2f} ms")
    print(f"Results: {results_dir / 'sample_orchestrator_latest.md'}")
    return 0 if valid_count == len(results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark only the AI orchestrator on sample_requests.csv.")
    parser.add_argument("--no-models", action="store_true", help="Use deterministic fallback and disable all providers.")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
