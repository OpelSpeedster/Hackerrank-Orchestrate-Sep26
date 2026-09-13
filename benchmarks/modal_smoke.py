from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from metrics import PipelineMetrics  # noqa: E402
from modal_client import ModalClient  # noqa: E402


async def run(endpoint: str) -> int:
    os.environ["MODAL_ENDPOINT"] = endpoint
    metrics = PipelineMetrics(
        extraction_model=os.getenv("EXTRACTION_MODEL", "qwen/qwen3.8-27b"),
        guard_model=os.getenv("ORCHESTRATOR_MODEL", os.getenv("REASONING_MODEL", "gpt-5.6-luna")),
        modal_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
    )
    client = ModalClient(timeout_seconds=float(os.getenv("MODAL_TIMEOUT_SECONDS", "120")), metrics=metrics)
    vectors = await client.embed(["pending salary credit", "recurring essential expense"])
    if not vectors:
        print("Modal smoke test failed: no embeddings returned.")
        return 1
    print("Modal smoke test passed.")
    print(f"Endpoint configured: {client.enabled}")
    print(f"Embedding count: {len(vectors)}")
    print(f"Embedding dimensions: {len(vectors[0])}")
    print(f"Modal calls: {metrics.modal_calls}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a deployed Modal embedding endpoint.")
    parser.add_argument("--endpoint", default=os.getenv("MODAL_ENDPOINT", ""))
    args = parser.parse_args()
    if not args.endpoint:
        print("Set MODAL_ENDPOINT or pass --endpoint.")
        return 2
    return asyncio.run(run(args.endpoint))


if __name__ == "__main__":
    raise SystemExit(main())
