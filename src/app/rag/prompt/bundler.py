from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from src.app.core.config import settings


def bundle_and_write(query: str, contexts: list[dict], prompt: list[dict], provider: str, model: str) -> str:
    row = {
        "ts": datetime.utcnow().isoformat(),
        "query": query,
        "contexts": contexts,
        "prompt": prompt,
        "provider": provider,
        "model": model,
    }
    table = pa.Table.from_pylist([row])
    day = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir = Path(settings.bundles_dir) / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"bundle-{datetime.utcnow().strftime('%H%M%S')}.parquet"
    pq.write_table(table, out_path)
    return str(out_path)
