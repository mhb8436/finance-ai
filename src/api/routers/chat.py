"""Chat API endpoints for AI Q&A."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    context: dict | None = None  # Optional context like current stock being viewed


class ChatResponse(BaseModel):
    response: str
    sources: list[dict] = []


@router.post("/query")
async def chat_query(request: ChatRequest) -> ChatResponse:
    """Send a chat query and get a response."""
    try:
        from src.agents.chat import ChatAgent

        agent = ChatAgent()
        result = await agent.chat(
            message=request.message,
            history=[msg.model_dump() for msg in request.history],
            context=request.context,
        )

        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """WebSocket for streaming chat responses."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") == "message":
                from src.agents.chat import ChatAgent

                agent = ChatAgent()

                # Stream response
                async for chunk in agent.stream_chat(
                    message=data.get("message", ""),
                    history=data.get("history", []),
                    context=data.get("context"),
                ):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk,
                    })

                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
