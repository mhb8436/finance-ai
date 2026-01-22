"""YouTube API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class TranscriptRequest(BaseModel):
    video_url: str
    languages: list[str] | None = None
    store_to_rag: bool = False
    kb_name: str = "youtube"


class TranscriptResponse(BaseModel):
    success: bool
    video_id: str | None = None
    title: str | None = None
    channel_name: str | None = None
    language: str | None = None
    duration_minutes: float | None = None
    text: str | None = None
    text_preview: str | None = None
    stored_to_rag: bool = False
    kb_name: str | None = None
    error: str | None = None


class ChannelVideosRequest(BaseModel):
    channel: str  # Channel ID, handle (@name), preset name, or URL
    max_results: int = 10


class VideoItem(BaseModel):
    video_id: str
    title: str
    channel_name: str
    published: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    url: str


class ChannelVideosResponse(BaseModel):
    success: bool
    channel: str
    video_count: int
    videos: list[VideoItem]
    error: str | None = None


class ChannelTranscriptsRequest(BaseModel):
    channel: str
    max_videos: int = 5
    languages: list[str] | None = None
    kb_name: str = "youtube"


@router.post("/transcript")
async def get_transcript(request: TranscriptRequest) -> TranscriptResponse:
    """Get transcript from a YouTube video.

    Works without API key. Requires video to have captions/subtitles.
    """
    try:
        from src.tools.youtube_tool import (
            get_transcript as fetch_transcript,
            get_transcript_and_store_to_rag,
        )

        if request.store_to_rag:
            result = await get_transcript_and_store_to_rag(
                video_url_or_id=request.video_url,
                kb_name=request.kb_name,
                languages=request.languages,
            )

            if result.get("success"):
                return TranscriptResponse(
                    success=True,
                    video_id=result.get("video_id"),
                    title=result.get("title"),
                    channel_name=result.get("channel_name"),
                    language=result.get("language"),
                    duration_minutes=result.get("duration_minutes"),
                    stored_to_rag=True,
                    kb_name=request.kb_name,
                )
            else:
                return TranscriptResponse(
                    success=False,
                    error=result.get("error", "Unknown error"),
                )
        else:
            transcript = await fetch_transcript(
                video_url_or_id=request.video_url,
                languages=request.languages,
            )

            if transcript:
                text_preview = transcript.text[:2000]
                if len(transcript.text) > 2000:
                    text_preview += "..."

                return TranscriptResponse(
                    success=True,
                    video_id=transcript.video_id,
                    title=transcript.title,
                    channel_name=transcript.channel_name,
                    language=transcript.language,
                    duration_minutes=round(transcript.duration_seconds / 60, 1),
                    text=transcript.text,
                    text_preview=text_preview,
                )
            else:
                return TranscriptResponse(
                    success=False,
                    error="Could not get transcript. Video may not have captions.",
                )

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail="youtube-transcript-api not installed. Run: pip install youtube-transcript-api",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channel/videos")
async def get_channel_videos(request: ChannelVideosRequest) -> ChannelVideosResponse:
    """Get recent videos from a YouTube channel.

    Supports:
    - Preset names: 삼프로TV, 슈카월드, 신사임당, etc.
    - Channel handles: @3protv
    - Channel IDs: UC8hoHG_eT8EK8ZkdrjpOVVw
    - Channel URLs
    """
    try:
        from src.tools.youtube_tool import get_channel_videos as fetch_videos

        videos = await fetch_videos(
            channel_identifier=request.channel,
            max_results=request.max_results,
        )

        return ChannelVideosResponse(
            success=True,
            channel=request.channel,
            video_count=len(videos),
            videos=[
                VideoItem(
                    video_id=v.video_id,
                    title=v.title,
                    channel_name=v.channel_name,
                    published=v.published,
                    description=v.description,
                    thumbnail_url=v.thumbnail_url,
                    url=v.url or f"https://www.youtube.com/watch?v={v.video_id}",
                )
                for v in videos
            ],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channel/transcripts")
async def get_channel_transcripts(
    request: ChannelTranscriptsRequest,
) -> dict[str, Any]:
    """Get transcripts from recent channel videos and store in RAG.

    Fetches recent videos from a channel, extracts transcripts,
    and stores them in the specified knowledge base.
    """
    try:
        from src.tools.youtube_tool import get_channel_videos_and_store_to_rag

        result = await get_channel_videos_and_store_to_rag(
            channel_identifier=request.channel,
            kb_name=request.kb_name,
            max_videos=request.max_videos,
            languages=request.languages,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/presets")
async def list_preset_channels() -> dict[str, Any]:
    """List preset Korean investment YouTube channels."""
    from src.tools.youtube_tool import get_channel_presets

    presets = get_channel_presets()

    return {
        "channels": [
            {
                "name": name,
                "channel_id": info["channel_id"],
                "description": info["description"],
            }
            for name, info in presets.items()
        ],
    }
