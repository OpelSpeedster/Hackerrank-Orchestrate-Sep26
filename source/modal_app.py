"""Deployable Modal web endpoint for FAISS embeddings.

Deploy from the repository root with:

    modal deploy source/modal_app.py

The deployment prints a callable .modal.run URL. Put that URL in MODAL_ENDPOINT;
MODAL_TOKEN_ID and MODAL_TOKEN_SECRET authenticate the Modal CLI deployment and
are not embedded in this application.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import modal

APP_NAME = "buy-wait-financial-embeddings"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("sentence-transformers", "Pillow", "fastapi[standard]")
)
app = modal.App(APP_NAME)

_model = None


def _embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


@app.function(image=image, timeout=120)
@modal.fastapi_endpoint(method="POST")
def inference(payload: dict[str, Any]) -> dict[str, Any]:
    task = str(payload.get("task", ""))
    if task == "embed":
        texts = payload.get("texts")
        if not isinstance(texts, list) or not all(isinstance(value, str) for value in texts):
            return {"error": "texts must be a list of strings"}
        model = _embedding_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        return {
            "task": task,
            "model": MODEL_NAME,
            "embeddings": vectors.tolist(),
        }

    if task == "financial_evidence_extraction":
        # Document extraction remains on the configured Qwen/Groq path by default.
        # This explicit response prevents a silent no-op if the endpoint is called for it.
        return {
            "task": task,
            "status": "unsupported_on_embedding_endpoint",
            "image_id": payload.get("image_id"),
            "related_event_id": payload.get("related_event_id"),
        }

    return {"error": f"unsupported task: {task}"}
