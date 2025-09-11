from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/ingest")


@router.post("/trigger")
def trigger_ingest():
    # TODO: implement background task to run CLI ingest
    return {"status": "accepted"}
