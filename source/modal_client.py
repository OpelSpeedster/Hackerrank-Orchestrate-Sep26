from __future__ import annotations

import asyncio
import base64
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Optional


class ModalClient:
    """Optional HTTP adapter for a Modal-served extraction/embedding endpoint."""

    def __init__(self, timeout_seconds: float = 30.0):
        self.api_key = os.getenv("MODAL_API_KEY", "").strip()
        self.endpoint = os.getenv("MODAL_ENDPOINT", "").strip().rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.endpoint)

    def _post(self, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not self.enabled:
            return None
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
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
