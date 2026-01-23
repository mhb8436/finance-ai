"""Research Pipeline API endpoints.

Provides endpoints for:
- Legacy research generation (backward compatible)
- New research pipeline with multi-agent orchestration
- Real-time progress streaming via WebSocket
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Data Models
# =============================================================================


class ResearchDepth(str, Enum):
    """Research depth levels."""
    QUICK = "quick"
    MEDIUM = "medium"
    DEEP = "deep"


class ResearchStatus(str, Enum):
    """Research job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchRequest(BaseModel):
    """Legacy research request (backward compatible)."""
    topic: str
    symbols: list[str] = []
    market: str = "US"
    depth: str = "medium"


class ResearchResponse(BaseModel):
    """Legacy research response."""
    research_id: str
    topic: str
    status: str
    report_path: str | None = None


class PipelineResearchRequest(BaseModel):
    """Pipeline research request."""
    topic: str = Field(..., description="Research topic or question")
    symbols: list[str] = Field(default=[], description="Stock symbols to analyze")
    market: str = Field(default="US", description="Target market: US, KR, or Both")
    context: str = Field(default="", description="Additional context or constraints")
    skip_rephrase: bool = Field(default=False, description="Skip topic optimization step")
    output_format: str = Field(default="markdown", description="Report format: markdown, json, html")
    max_topics: int = Field(default=10, ge=1, le=20, description="Maximum sub-topics to research")
    language: str = Field(default="ko", description="Report language: ko (Korean) or en (English)")


class PipelineResearchResponse(BaseModel):
    """Pipeline research creation response."""
    research_id: str
    topic: str
    status: ResearchStatus
    message: str
    created_at: str


class ResearchStatusResponse(BaseModel):
    """Research status response."""
    research_id: str
    status: ResearchStatus
    topic: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    current_stage: str | None = None
    progress: dict[str, Any] | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


class ResearchListItem(BaseModel):
    """Research list item."""
    research_id: str
    topic: str
    status: ResearchStatus
    created_at: str
    completed_at: str | None = None


# =============================================================================
# In-Memory Research Job Store
# =============================================================================


class ResearchJobStore:
    """In-memory store for research jobs.

    In production, this should be replaced with Redis or a database.
    """

    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def create(self, research_id: str, topic: str, request: PipelineResearchRequest) -> dict:
        """Create a new research job."""
        async with self._lock:
            job = {
                "research_id": research_id,
                "topic": topic,
                "status": ResearchStatus.PENDING,
                "request": request.model_dump(),
                "created_at": datetime.utcnow().isoformat(),
                "started_at": None,
                "completed_at": None,
                "current_stage": None,
                "progress": {},
                "error": None,
                "result": None,
            }
            self._jobs[research_id] = job
            return job

    async def get(self, research_id: str) -> dict | None:
        """Get a research job by ID."""
        return self._jobs.get(research_id)

    async def update(self, research_id: str, **updates) -> dict | None:
        """Update a research job."""
        async with self._lock:
            if research_id not in self._jobs:
                return None
            self._jobs[research_id].update(updates)

            # Notify subscribers
            if research_id in self._subscribers:
                event = {"type": "update", "data": self._jobs[research_id]}
                for queue in self._subscribers[research_id]:
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        pass

            return self._jobs[research_id]

    async def list_all(self, limit: int = 50) -> list[dict]:
        """List all research jobs."""
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        return jobs[:limit]

    async def subscribe(self, research_id: str) -> asyncio.Queue:
        """Subscribe to job updates."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        if research_id not in self._subscribers:
            self._subscribers[research_id] = []
        self._subscribers[research_id].append(queue)
        return queue

    async def unsubscribe(self, research_id: str, queue: asyncio.Queue):
        """Unsubscribe from job updates."""
        if research_id in self._subscribers:
            try:
                self._subscribers[research_id].remove(queue)
            except ValueError:
                pass


# Global job store
_job_store = ResearchJobStore()


# =============================================================================
# Background Task: Run Pipeline
# =============================================================================


async def run_pipeline_task(research_id: str, request: PipelineResearchRequest):
    """Background task to run the research pipeline."""
    try:
        # Update status to running
        await _job_store.update(
            research_id,
            status=ResearchStatus.RUNNING,
            started_at=datetime.utcnow().isoformat(),
        )

        # Import and create pipeline
        from src.tools.pipeline_tools import create_configured_pipeline

        pipeline = create_configured_pipeline(
            max_topics=request.max_topics,
        )

        # Run with streaming to capture progress
        stage_map = {
            "started": "Initializing",
            "rephrase": "Optimizing topic",
            "decompose": "Decomposing into sub-topics",
            "research_start": "Researching",
            "research_complete": "Research completed",
            "notes": "Creating notes",
            "report": "Generating report",
            "completed": "Completed",
        }

        async for event in pipeline.run_streaming(
            topic=request.topic,
            context=request.context,
            symbols=request.symbols,
            market=request.market,
            language=request.language,
        ):
            event_type = event.get("event", "")
            stage = event.get("stage", event_type)

            progress = {
                "event": event_type,
                "stage": stage,
                "details": event,
            }

            await _job_store.update(
                research_id,
                current_stage=stage_map.get(event_type, stage),
                progress=progress,
            )

            # Extract report if available (before completed to preserve it)
            if event_type == "stage_complete" and event.get("stage") == "report":
                report = event.get("report", {})
                await _job_store.update(
                    research_id,
                    result={"report": report},
                )

            # If completed, merge final result with existing (preserving report)
            if event_type == "completed":
                # Get final result
                result = pipeline.get_current_state()

                # Get existing job to preserve report
                existing_job = await _job_store.get(research_id)
                existing_result = existing_job.get("result", {}) if existing_job else {}

                final_result = {
                    **existing_result,  # Preserve existing data (including report)
                    "statistics": event.get("statistics", {}),
                    "queue_state": result.get("queue", {}) if result else {},
                }

                await _job_store.update(
                    research_id,
                    status=ResearchStatus.COMPLETED,
                    completed_at=datetime.utcnow().isoformat(),
                    result=final_result,
                )

        logger.info(f"Research pipeline completed: {research_id}")

    except Exception as e:
        logger.error(f"Research pipeline failed: {research_id} - {e}")
        await _job_store.update(
            research_id,
            status=ResearchStatus.FAILED,
            completed_at=datetime.utcnow().isoformat(),
            error=str(e),
        )


# =============================================================================
# Legacy Endpoints (Backward Compatible)
# =============================================================================


@router.post("/generate")
async def generate_research(request: ResearchRequest) -> ResearchResponse:
    """Generate a research report (legacy endpoint).

    Uses the legacy ResearchAgent for backward compatibility.
    For new integrations, use POST /pipeline instead.
    """
    try:
        from src.agents.research import ResearchAgent

        research_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        agent = ResearchAgent()
        result = await agent.research(
            topic=request.topic,
            symbols=request.symbols,
            market=request.market,
            depth=request.depth,
            research_id=research_id,
        )

        return ResearchResponse(
            research_id=research_id,
            topic=request.topic,
            status="completed",
            report_path=result.get("report_path"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{research_id}")
async def research_websocket(websocket: WebSocket, research_id: str):
    """WebSocket for real-time research progress (legacy).

    For new integrations, use /stream/{research_id} instead.
    """
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected", "research_id": research_id})

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass


@router.get("/list")
async def list_research() -> list[dict]:
    """List all research reports (legacy).

    Lists reports from file system for backward compatibility.
    For pipeline research, use GET /pipeline/list.
    """
    from pathlib import Path
    from src.core.config import get_project_root

    reports_dir = get_project_root() / "data" / "user" / "research"
    reports = []

    if reports_dir.exists():
        for report_file in reports_dir.glob("*.md"):
            reports.append({
                "id": report_file.stem,
                "filename": report_file.name,
                "created": report_file.stat().st_mtime,
            })

    return sorted(reports, key=lambda x: x["created"], reverse=True)


# =============================================================================
# Pipeline Endpoints (New)
# =============================================================================


@router.post("/pipeline", response_model=PipelineResearchResponse)
async def start_pipeline_research(
    request: PipelineResearchRequest,
    background_tasks: BackgroundTasks,
) -> PipelineResearchResponse:
    """Start a new research pipeline.

    This endpoint initiates a multi-agent research pipeline that:
    1. Rephrases the topic for clarity (optional)
    2. Decomposes into sub-topics
    3. Researches each sub-topic with various tools
    4. Creates notes from findings
    5. Generates a comprehensive report

    The research runs in the background. Use GET /pipeline/{id} to check status
    or WebSocket /stream/{id} for real-time updates.

    Args:
        request: Pipeline research request with topic, symbols, etc.

    Returns:
        Response with research_id for tracking.
    """
    research_id = f"pipeline_{uuid.uuid4().hex[:12]}"

    # Create job in store
    await _job_store.create(research_id, request.topic, request)

    # Start background task
    background_tasks.add_task(run_pipeline_task, research_id, request)

    return PipelineResearchResponse(
        research_id=research_id,
        topic=request.topic,
        status=ResearchStatus.PENDING,
        message="Research pipeline started. Use GET /pipeline/{id} or WebSocket /stream/{id} to track progress.",
        created_at=datetime.utcnow().isoformat(),
    )


@router.get("/pipeline/{research_id}", response_model=ResearchStatusResponse)
async def get_pipeline_status(research_id: str) -> ResearchStatusResponse:
    """Get the status of a research pipeline.

    Args:
        research_id: The research ID returned from POST /pipeline.

    Returns:
        Current status, progress, and results if completed.
    """
    job = await _job_store.get(research_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Research not found: {research_id}")

    return ResearchStatusResponse(
        research_id=job["research_id"],
        status=job["status"],
        topic=job["topic"],
        created_at=job["created_at"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        current_stage=job["current_stage"],
        progress=job["progress"],
        error=job["error"],
        result=job["result"],
    )


@router.get("/pipeline/list/all", response_model=list[ResearchListItem])
async def list_pipeline_research(limit: int = 50) -> list[ResearchListItem]:
    """List all pipeline research jobs.

    Args:
        limit: Maximum number of jobs to return (default 50).

    Returns:
        List of research jobs with basic info.
    """
    jobs = await _job_store.list_all(limit=limit)

    return [
        ResearchListItem(
            research_id=job["research_id"],
            topic=job["topic"],
            status=job["status"],
            created_at=job["created_at"],
            completed_at=job["completed_at"],
        )
        for job in jobs
    ]


@router.websocket("/stream/{research_id}")
async def stream_pipeline_progress(websocket: WebSocket, research_id: str):
    """WebSocket for real-time research pipeline progress.

    Streams progress events as JSON:
    - {"type": "connected", "research_id": "..."}
    - {"type": "update", "data": {...}}
    - {"type": "completed", "result": {...}}
    - {"type": "error", "message": "..."}

    Args:
        research_id: The research ID to stream updates for.
    """
    await websocket.accept()

    # Check if research exists
    job = await _job_store.get(research_id)
    if not job:
        await websocket.send_json({"type": "error", "message": f"Research not found: {research_id}"})
        await websocket.close()
        return

    # Send current state
    await websocket.send_json({"type": "connected", "research_id": research_id})
    await websocket.send_json({"type": "current_state", "data": job})

    # If already completed or failed, close
    if job["status"] in (ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED):
        await websocket.send_json({
            "type": "final",
            "status": job["status"],
            "result": job["result"],
            "error": job["error"],
        })
        await websocket.close()
        return

    # Subscribe to updates
    queue = await _job_store.subscribe(research_id)

    try:
        while True:
            # Wait for updates with timeout
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)

                # Check if completed
                if event.get("type") == "update":
                    data = event.get("data", {})
                    status = data.get("status")
                    if status in (ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED):
                        await websocket.send_json({
                            "type": "final",
                            "status": status,
                            "result": data.get("result"),
                            "error": data.get("error"),
                        })
                        break

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {research_id}")
    finally:
        await _job_store.unsubscribe(research_id, queue)


@router.delete("/pipeline/{research_id}")
async def cancel_pipeline_research(research_id: str) -> dict:
    """Cancel a running research pipeline.

    Note: This marks the job as cancelled but does not immediately stop
    the background task. The task will check for cancellation at checkpoints.

    Args:
        research_id: The research ID to cancel.

    Returns:
        Confirmation message.
    """
    job = await _job_store.get(research_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Research not found: {research_id}")

    if job["status"] in (ResearchStatus.COMPLETED, ResearchStatus.FAILED, ResearchStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel research with status: {job['status']}",
        )

    await _job_store.update(
        research_id,
        status=ResearchStatus.CANCELLED,
        completed_at=datetime.utcnow().isoformat(),
    )

    return {"message": f"Research cancelled: {research_id}"}


# =============================================================================
# Utility Endpoints
# =============================================================================


@router.get("/tools")
async def list_available_tools() -> dict[str, Any]:
    """List available research tools.

    Returns:
        Dictionary of tool names and descriptions.
    """
    from src.tools.pipeline_tools import get_tool_descriptions, get_pipeline_tool_handlers

    handlers = get_pipeline_tool_handlers()

    return {
        "tools": list(handlers.keys()),
        "descriptions": get_tool_descriptions(),
    }
