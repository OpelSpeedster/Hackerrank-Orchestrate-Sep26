from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass
class RequestMetric:
    request_id: str
    latency_ms: float
    valid: bool
    fallback_used: bool
    planned_steps: int
    attempted_tools: int
    successful_tools: int
    model_calls: int
    guard_flagged: bool = False
    guard_status: str = "disabled"
    qwen_status: str = "disabled"
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineMetrics:
    extraction_model: str
    guard_model: str
    modal_model: str = ""
    provider: str = "Groq + Modal"
    run_id: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_metrics: list[RequestMetric] = field(default_factory=list)
    model_calls: int = 0
    successful_model_calls: int = 0
    guard_calls: int = 0
    extraction_calls: int = 0
    modal_calls: int = 0
    modal_successes: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    guard_flagged: int = 0
    guard_completed: int = 0
    guard_failed: int = 0
    guard_timed_out: int = 0
    guard_invalid_response: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: Decimal = Decimal("0")
    error_counts: dict[str, int] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def model_call(
        self,
        kind: str,
        success: bool,
        response: Any = None,
        input_rate: Decimal = Decimal("0"),
        output_rate: Decimal = Decimal("0"),
        timed_out: bool = False,
        error_kind: str | None = None,
    ) -> None:
        prompt = completion = 0
        details = getattr(response, "usage", None) if response is not None else None
        if details is not None:
            prompt = int(getattr(details, "prompt_tokens", 0) or 0)
            completion = int(getattr(details, "completion_tokens", 0) or 0)
        with self._lock:
            self.model_calls += 1
            self.input_tokens += prompt
            self.output_tokens += completion
            self.estimated_cost_usd += (
                Decimal(prompt) / Decimal(1_000_000) * input_rate
                + Decimal(completion) / Decimal(1_000_000) * output_rate
            )
            if success:
                self.successful_model_calls += 1
            if kind == "guard":
                self.guard_calls += 1
            elif kind == "extraction":
                self.extraction_calls += 1
            if not success:
                self.failed_calls += 1
            if timed_out:
                self.timeout_calls += 1
            if error_kind:
                self.error_counts[error_kind] = self.error_counts.get(error_kind, 0) + 1

    def modal_call(self, success: bool, error_kind: str | None = None) -> None:
        with self._lock:
            self.modal_calls += 1
            if success:
                self.modal_successes += 1
            else:
                self.failed_calls += 1
            if error_kind:
                self.error_counts[error_kind] = self.error_counts.get(error_kind, 0) + 1

    def record_guard(self, flagged: bool, status: str) -> None:
        with self._lock:
            if status == "completed":
                self.guard_completed += 1
            elif status == "timeout":
                self.guard_timed_out += 1
            elif status == "invalid_response":
                self.guard_invalid_response += 1
            elif status == "failed":
                self.guard_failed += 1
            if flagged:
                self.guard_flagged += 1

    def record_request(self, metric: RequestMetric) -> None:
        with self._lock:
            self.request_metrics.append(metric)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{path.stem}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)

    def write_reports(self, root: Path, output_path: Path) -> None:
        latencies = sorted(item.latency_ms for item in self.request_metrics)
        requests = len(self.request_metrics)
        total_tokens = self.input_tokens + self.output_tokens
        average_tokens = (Decimal(total_tokens) / requests) if requests else Decimal("0")
        average_latency = mean(latencies) if latencies else 0.0
        p50 = latencies[(len(latencies) - 1) // 2] if latencies else 0.0
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0
        fallback_count = sum(item.fallback_used for item in self.request_metrics)
        cost_per_request = self.estimated_cost_usd / requests if requests else Decimal("0")
        output_hash = "missing"
        if output_path.exists():
            output_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
        safety_rate = (
            f"{self.guard_flagged / self.guard_completed:.4%}"
            if self.guard_completed
            else "unavailable (no completed Guard calls)"
        )
        error_summary = ", ".join(
            f"{name}={count}" for name, count in sorted(self.error_counts.items())
        ) or "none"
        lines = [
            "# Model Usage and Evaluation Report",
            "",
            f"Run ID: `{self.run_id}`",
            f"Generated at (UTC): `{self.generated_at}`",
            f"Output: `{output_path}`",
            f"Output SHA-256: `{output_hash}`",
            "",
            "## Providers and models",
            "",
            f"- Provider: `{self.provider}`",
            f"- Qwen extraction model: `{self.extraction_model}`",
            f"- Orchestrator model: `{self.guard_model}`",
            f"- Modal embedding/document model: `{self.modal_model or 'not configured'}`",
            "- Modal calls are enabled when `MODAL_ENDPOINT` is configured; deployment tokens remain environment-only.",
            "",
            "## Requests and latency",
            "",
            f"- Requests processed: {requests}",
            f"- Valid requests: {sum(item.valid for item in self.request_metrics)}",
            f"- Fallback requests: {fallback_count}",
            f"- Average latency (ms): {average_latency:.2f}",
            f"- P50 latency (ms): {p50:.2f}",
            f"- P95 latency (ms): {p95:.2f}",
            "",
            "## Model usage",
            "",
            f"- Total provider model calls: {self.model_calls + self.modal_calls}",
            f"- Groq model calls: {self.model_calls}",
            f"- Modal calls: {self.modal_calls}",
            f"- Successful model calls: {self.successful_model_calls + self.modal_successes}",
            f"- Orchestrator calls attempted: {self.guard_calls}",
            f"- Qwen image extraction calls attempted: {self.extraction_calls}",
            f"- Failed provider calls: {self.failed_calls}",
            f"- Timed-out Groq calls: {self.timeout_calls}",
            f"- Input tokens: {self.input_tokens}",
            f"- Output tokens: {self.output_tokens}",
            f"- Total tokens: {total_tokens}",
            f"- Average tokens per request: {average_tokens:.2f}",
            f"- Estimated provider cost (USD): {self.estimated_cost_usd:.8f}",
            f"- Estimated cost per request (USD): {cost_per_request:.8f}",
            f"- Model error categories: {error_summary}",
            "",
            "## Safety and orchestration metrics",
            "",
            f"- Guard calls attempted: {self.guard_calls}",
            f"- Completed safety calls: {self.guard_completed}",
            f"- Failed safety calls: {self.guard_failed}",
            f"- Timed-out safety calls: {self.guard_timed_out}",
            f"- Invalid safety responses: {self.guard_invalid_response}",
            f"- Flagged requests: {self.guard_flagged}",
            f"- Safety flag rate: {safety_rate}",
            "",
            "## Per-request execution",
            "",
            "| request_id | latency_ms | valid | fallback | planned_steps | attempted_tools | successful_tools | model_calls | guard_status | qwen_status | guard_flagged | errors |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|",
        ]
        for item in sorted(self.request_metrics, key=lambda value: value.request_id):
            errors = ", ".join(item.errors).replace("|", "/")
            lines.append(
                f"| {item.request_id} | {item.latency_ms:.2f} | {item.valid} | "
                f"{item.fallback_used} | {item.planned_steps} | {item.attempted_tools} | "
                f"{item.successful_tools} | {item.model_calls} | {item.guard_status} | "
                f"{item.qwen_status} | {item.guard_flagged} | {errors} |"
            )
        report = "\n".join(lines) + "\n"
        for path in (root / "evaluation" / "usage_report.md", root / "code" / "evaluation" / "usage_report.md"):
            self._atomic_write(path, report)
