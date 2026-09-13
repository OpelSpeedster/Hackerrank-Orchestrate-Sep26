from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable

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
    """Metadata-filtered FAISS index with a dependency-free lexical fallback."""

    def __init__(self, dataset: Dataset, dimensions: int = 256):
        self.dimensions = dimensions
        self.documents: list[EvidenceDocument] = []
        self._index = None
        self._vectors = None
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

    def _build_index(self) -> None:
        if not self.documents or np is None:
            return
        vectors = np.vstack([self._vector(document.text) for document in self.documents])
        self._vectors = vectors
        if faiss is not None:
            self._index = faiss.IndexFlatIP(self.dimensions)
            self._index.add(vectors)

    @staticmethod
    def _lexical_score(query: str, text: str) -> float:
        query_tokens = set(_TOKEN_RE.findall(query.lower()))
        text_tokens = set(_TOKEN_RE.findall(text.lower()))
        if not query_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / math.sqrt(len(query_tokens) * max(1, len(text_tokens)))

    def search(
        self,
        query: str,
        user_id: str,
        request_id: str = "",
        event_ids: Iterable[str] = (),
        limit: int = 8,
    ) -> list[dict]:
        allowed_events = set(event_ids)
        eligible = [
            index
            for index, document in enumerate(self.documents)
            if document.user_id == user_id
            and (not request_id or not document.request_id or document.request_id == request_id)
            and (not allowed_events or not document.event_id or document.event_id in allowed_events)
        ]
        if not eligible:
            return []

        scores: list[tuple[float, int]] = []
        query_vector = self._vector(query)
        if self._index is not None and query_vector is not None:
            distances, indices = self._index.search(query_vector.reshape(1, -1), len(self.documents))
            score_by_index = {int(index): float(score) for score, index in zip(distances[0], indices[0])}
            scores = [(score_by_index.get(index, 0.0), index) for index in eligible]
        else:
            scores = [(self._lexical_score(query, self.documents[index].text), index) for index in eligible]
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
