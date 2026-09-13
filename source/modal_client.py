from __future__ import annotations

import asyncio
import base64
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Optional

from metrics import PipelineMetrics


class ModalClient:
    """Optional HTTP adapter for a Modal-served extraction/embedding endpoint."""

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        metrics: PipelineMetrics | None = None,
        enabled_override: bool | None = None,
    ):
        self.token_id = os.getenv("MODAL_TOKEN_ID", "").strip()
        self.token_secret = os.getenv("MODAL_TOKEN_SECRET", "").strip()
        self.endpoint_token = os.getenv("MODAL_ENDPOINT_TOKEN", "").strip()
        self.endpoint = os.getenv("MODAL_ENDPOINT", "").strip().rstrip("/")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "")
        self.timeout_seconds = timeout_seconds
        self.metrics = metrics
        self.enabled_override = enabled_override

    @property
    def enabled(self) -> bool:
        if self.enabled_override is False:
            return False
        return bool(self.endpoint)

    def _post(self, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not self.enabled:
            return None
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.endpoint_token:
            request.add_header("Authorization", f"Bearer {self.endpoint_token}")
        elif self.token_id and self.token_secret:
            request.add_header("X-Modal-Token-Id", self.token_id)
            request.add_header("X-Modal-Token-Secret", self.token_secret)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            if self.metrics:
                self.metrics.modal_call(isinstance(data, dict))
            return data if isinstance(data, dict) else None
        except Exception:
            if self.metrics:
                self.metrics.modal_call(False, "modal_provider_error")
            return None

    async def extract_document(self, image_path: Path, image_id: str, related_event_id: str) -> Optional[dict[str, Any]]:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "task": "financial_evidence_extraction",
            "image_id": image_id,
            "related_event_id": related_event_id,
            "image_base64": encoded,
        }
        return await asyncio.to_thread(self._post, payload)

    async def embed(self, texts: list[str]) -> Optional[list[list[float]]]:
        data = await asyncio.to_thread(self._post, {"task": "embed", "texts": texts})
        if not data or not isinstance(data.get("embeddings"), list):
            return None
        return data["embeddings"]
