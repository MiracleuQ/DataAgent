import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.core.context import DataContext
from app.factory import create_system


router = APIRouter(prefix="/api/v1", tags=["analysis"])


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="Natural language analysis request")
    data_context_id: Optional[str] = Field(None, description="Existing data context ID")


class AnalysisResponse(BaseModel):
    status: str
    report: str = ""
    review: str = ""
    charts: list = []
    artifacts: list = []
    errors: dict = {}
    execution: dict = {}


class DataUploadResponse(BaseModel):
    status: str
    name: str
    rows: int
    columns: int
    context_id: str


_system_cache = None
_context_store: Dict[str, DataContext] = {}


def get_system():
    global _system_cache
    if _system_cache is None:
        _system_cache = create_system()
    return _system_cache


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    try:
        coordinator, orchestrator = get_system()
        context = _context_store.get(request.data_context_id) if request.data_context_id else DataContext()
        if context is None:
            context = DataContext()
        result = await orchestrator.run(
            user_request=request.query,
            context=context,
            coordinator=coordinator,
        )
        return AnalysisResponse(
            status=result.get("status", "success"),
            report=result.get("report", ""),
            review=result.get("review", ""),
            charts=result.get("charts", []),
            artifacts=result.get("artifacts", []),
            errors=result.get("errors", {}),
            execution=result.get("execution", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DataUploadResponse)
async def upload_data(file: UploadFile = File(...)):
    import pandas as pd
    import uuid
    try:
        content = await file.read()
        name = file.filename.rsplit(".", 1)[0]
        context_id = str(uuid.uuid4())

        if file.filename.endswith(".csv"):
            import io
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            import io
            df = pd.read_excel(io.BytesIO(content))
        elif file.filename.endswith(".json"):
            import io
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        context = DataContext()
        context.add_dataframe(name, df, auto_profile=True)
        _context_store[context_id] = context

        return DataUploadResponse(
            status="success",
            name=name,
            rows=len(df),
            columns=len(df.columns),
            context_id=context_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/stats")
async def get_stats():
    coordinator, orchestrator = get_system()
    return {
        "agents": list(orchestrator._agents.keys()),
        "execution_events": len(orchestrator.execution_events),
    }
