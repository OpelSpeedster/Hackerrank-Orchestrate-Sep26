from __future__ import annotations

import asyncio
import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable

try:
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - deterministic lexical fallback
    np = None

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    faiss = None

from models import Dataset

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class EvidenceDocument:
    record_id: str
    user_id: str
    record_type: str
    text: str
    request_id: str = ""
    event_id: str = ""
    event_date: str = ""


class EvidenceIndex:
    """Metadata-filtered FAISS index with Modal and lexical fallbacks."""

    def __init__(self, dataset: Dataset, dimensions: int = 256):
        self.dimensions = dimensions
        self.documents: list[EvidenceDocument] = []
        self._index = None
        self._vectors = None
        self.remote_embeddings = False
        self._build_documents(dataset)
        self._build_index()

    def _build_documents(self, dataset: Dataset) -> None:
        for user_id, events in dataset.events_by_user.items():
            for event in events:
                self.documents.append(
                    EvidenceDocument(
                        record_id=event.event_id,
                        user_id=user_id,
                        record_type="financial_event",
                        event_id=event.event_id,
                        event_date=event.event_date,
                        text=(
                            f"{event.event_type} {event.category} {event.description} "
                            f"{event.direction} {event.status} {event.event_date}"
                        ),
                    )
                )
        for user_id, messages in dataset.messages_by_user.items():
            for message in messages:
                self.documents.append(
                    EvidenceDocument(
                        record_id=message.message_id,
                        user_id=user_id,
                        record_type="message",
                        request_id=message.request_id,
                        event_id=message.related_event_id,
                        text=message.message_text,
                    )
                )
        for request_id, images in dataset.images_by_request.items():
            for image in images:
                self.documents.append(
                    EvidenceDocument(
                        record_id=image.image_id,
                        user_id=image.user_id,
                        record_type="image",
                        request_id=request_id,
                        event_id=image.related_event_id,
                        text=f"image {image.image_id} related event {image.related_event_id}",
                    )
                )

    def _vector(self, text: str):
        if np is None:
            return None
        vector = np.zeros(self.dimensions, dtype="float32")
        for token in _TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector

    def _set_vectors(self, vectors: Any) -> bool:
        if np is None:
            return False
        values = np.asarray(vectors, dtype="float32")
        if values.ndim != 2 or len(values) != len(self.documents) or values.shape[1] == 0:
            return False
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        values = values / np.maximum(norms, 1e-12)
        self.dimensions = int(values.shape[1])
        self._vectors = values
        self._index = None
        if faiss is not None:
            self._index = faiss.IndexFlatIP(self.dimensions)
            self._index.add(values)
        return True

    def _build_index(self) -> None:
        if not self.documents or np is None:
            return
        self._set_vectors(np.vstack([self._vector(document.text) for document in self.documents]))

    async def build_remote_embeddings(self, embedder: Any, batch_size: int = 128) -> bool:
        """Replace hash vectors with Modal embeddings when explicitly configured."""
        if not getattr(embedder, "enabled", False) or not self.documents:
            return False
        vectors: list[list[float]] = []
        for start in range(0, len(self.documents), batch_size):
            batch = [document.text for document in self.documents[start : start + batch_size]]
            result = await embedder.embed(batch)
            if not result or len(result) != len(batch):
                return False
            vectors.extend(result)
        self.remote_embeddings = self._set_vectors(vectors)
        return self.remote_embeddings

    @staticmethod
    def _lexical_score(query: str, text: str) -> float:
        query_tokens = set(_TOKEN_RE.findall(query.lower()))
        text_tokens = set(_TOKEN_RE.findall(text.lower()))
        if not query_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / math.sqrt(len(query_tokens) * max(1, len(text_tokens)))

    def _eligible(self, user_id: str, request_id: str, event_ids: Iterable[str]) -> list[int]:
        allowed_events = set(event_ids)
        return [
            index
            for index, document in enumerate(self.documents)
            if document.user_id == user_id
            and (not request_id or not document.request_id or document.request_id == request_id)
            and (not allowed_events or not document.event_id or document.event_id in allowed_events)
        ]

    def _format_results(self, scores: list[tuple[float, int]], limit: int) -> list[dict]:
        scores.sort(key=lambda item: (-item[0], self.documents[item[1]].record_id))
        return [
            {
                "record_id": self.documents[index].record_id,
                "user_id": self.documents[index].user_id,
                "record_type": self.documents[index].record_type,
                "request_id": self.documents[index].request_id,
                "event_id": self.documents[index].event_id,
                "event_date": self.documents[index].event_date,
                "text": self.documents[index].text[:1000],
                "score": round(score, 6),
            }
            for score, index in scores[:limit]
            if score > 0
        ]

    def _search_vector(self, vector: Any, eligible: list[int], limit: int) -> list[dict]:
        if self._index is not None:
            distances, indices = self._index.search(vector.reshape(1, -1), len(self.documents))
            score_by_index = {int(index): float(score) for score, index in zip(distances[0], indices[0])}
            return self._format_results(
                [(score_by_index.get(index, 0.0), index) for index in eligible], limit
            )
        if self._vectors is not None and np is not None:
            scores = self._vectors[eligible] @ vector
            return self._format_results(
                [(float(score), index) for score, index in zip(scores, eligible)], limit
            )
        return []

    def search(
        self,
        query: str,
        user_id: str,
        request_id: str = "",
        event_ids: Iterable[str] = (),
        limit: int = 8,
    ) -> list[dict]:
        eligible = self._eligible(user_id, request_id, event_ids)
        if not eligible:
            return []
        query_vector = self._vector(query) if not self.remote_embeddings else None
        if query_vector is not None:
            return self._search_vector(query_vector, eligible, limit)
        return self._format_results(
            [(self._lexical_score(query, self.documents[index].text), index) for index in eligible],
            limit,
        )

    async def search_async(
        self,
        query: str,
        user_id: str,
        request_id: str = "",
        event_ids: Iterable[str] = (),
        limit: int = 8,
        embedder: Any = None,
    ) -> list[dict]:
        eligible = self._eligible(user_id, request_id, event_ids)
        if not eligible:
            return []
        if self.remote_embeddings and getattr(embedder, "enabled", False):
            response = await embedder.embed([query])
            if response and len(response) == 1 and np is not None:
                vector = np.asarray(response[0], dtype="float32")
                norm = float(np.linalg.norm(vector))
                if vector.ndim == 1 and len(vector) == self.dimensions and norm:
                    return self._search_vector(vector / norm, eligible, limit)
        return self.search(query, user_id, request_id, event_ids, limit)
