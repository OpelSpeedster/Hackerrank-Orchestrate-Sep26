from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
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
    tool_calls: int
    guard_flagged: bool = False
    guard_status: str = "disabled"
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineMetrics:
    extraction_model: str
    guard_model: str
    provider: str = "Groq"
    request_metrics: list[RequestMetric] = field(default_factory=list)
    model_calls: int = 0
    guard_calls: int = 0
    extraction_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    guard_flagged: int = 0
    guard_completed: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: Decimal = Decimal("0")
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def model_call(
        self,
        kind: str,
        success: bool,
        response: Any = None,
        input_rate: Decimal = Decimal("0"),
        output_rate: Decimal = Decimal("0"),
        timed_out: bool = False,
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
            if kind == "guard":
                self.guard_calls += 1
            elif kind == "extraction":
                self.extraction_calls += 1
            if not success:
                self.failed_calls += 1
            if timed_out:
                self.timeout_calls += 1

    def record_guard(self, flagged: bool, completed: bool) -> None:
        with self._lock:
            if completed:
                self.guard_completed += 1
            if flagged:
                self.guard_flagged += 1

    def record_request(self, metric: RequestMetric) -> None:
        with self._lock:
            self.request_metrics.append(metric)

    def write_reports(self, root: Path, output_path: Path) -> None:
        latencies = sorted(item.latency_ms for item in self.request_metrics)
        requests = len(self.request_metrics)
        total_tokens = self.input_tokens + self.output_tokens
        average_latency = mean(latencies) if latencies else 0.0
        p50 = latencies[(len(latencies) - 1) // 2] if latencies else 0.0
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0
        safety_rate = (self.guard_flagged / self.guard_completed) if self.guard_completed else 0.0
        fallback_count = sum(item.fallback_used for item in self.request_metrics)
        cost_per_request = self.estimated_cost_usd / requests if requests else Decimal("0")
        lines = [
            "# Model Usage and Evaluation Report",
            "",
            f"Output: `{output_path}`",
            "",
            "## Providers and models",
            "",
            f"- Provider: `{self.provider}`",
            f"- Qwen extraction model: `{self.extraction_model}`",
            f"- Meta safety/router model: `{self.guard_model}`",
            "- Modal is optional and is used only when `MODAL_API_KEY` and `MODAL_ENDPOINT` are configured.",
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
            f"- Total model calls: {self.model_calls}",
            f"- Llama/Meta safety calls: {self.guard_calls}",
            f"- Qwen image extraction calls: {self.extraction_calls}",
            f"- Failed model calls: {self.failed_calls}",
            f"- Timed-out model calls: {self.timeout_calls}",
            f"- Input tokens: {self.input_tokens}",
            f"- Output tokens: {self.output_tokens}",
            f"- Total tokens: {total_tokens}",
            f"- Estimated provider cost (USD): {self.estimated_cost_usd:.8f}",
            f"- Estimated cost per request (USD): {cost_per_request:.8f}",
            "",
            "## Safety metrics",
            "",
            f"- Completed safety calls: {self.guard_completed}",
            f"- Flagged requests: {self.guard_flagged}",
            f"- Safety flag rate: {safety_rate:.4%}",
            "",
            "## Per-request latency",
            "",
            "| request_id | latency_ms | valid | fallback | guard_status | guard_flagged | tool_calls | errors |",
            "|---|---:|---:|---:|---|---:|---:|---|",
        ]
        for item in sorted(self.request_metrics, key=lambda value: value.request_id):
            errors = ", ".join(item.errors).replace("|", "/")
            lines.append(
                f"| {item.request_id} | {item.latency_ms:.2f} | {item.valid} | "
                f"{item.fallback_used} | {item.guard_status} | {item.guard_flagged} | "
                f"{item.tool_calls} | {errors} |"
            )
        report = "\n".join(lines) + "\n"
        for path in (root / "evaluation" / "usage_report.md", root / "code" / "evaluation" / "usage_report.md"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
