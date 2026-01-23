"""YouTube Tools.

Provides YouTube video transcript extraction and channel video listing.
All features work without API key unless noted.

Features:
1. Transcript extraction (youtube-transcript-api, free)
2. Channel recent videos via RSS (free)
3. Popular Korean investment channel presets
"""

import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class YouTubeVideo:
    """YouTube video information."""

    video_id: str
    title: str
    channel_name: str
    channel_id: str | None = None
    published: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    url: str | None = None

    def __post_init__(self):
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "published": self.published,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url,
            "url": self.url,
        }


@dataclass
class YouTubeTranscript:
    """YouTube video transcript."""

    video_id: str
    title: str
    channel_name: str
    language: str
    text: str
    segments: list[dict[str, Any]]
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel_name": self.channel_name,
            "language": self.language,
            "text": self.text,
            "duration_seconds": self.duration_seconds,
            "segment_count": len(self.segments),
        }

    def to_text(self) -> str:
        """Convert to text for RAG indexing."""
        return f"""제목: {self.title}
채널: {self.channel_name}
URL: https://www.youtube.com/watch?v={self.video_id}
언어: {self.language}
길이: {self.duration_seconds / 60:.1f}분

--- 스크립트 ---
{self.text}
"""


# =============================================================================
# Popular Korean Investment YouTube Channels
# =============================================================================


KOREAN_INVESTMENT_CHANNELS = {
    # 채널명: (YouTube handle, 설명) - handle은 자동으로 채널 ID로 변환됨
    "삼프로TV": ("@3PROTV", "삼프로TV - 경제/투자 전문"),
    "슈카월드": ("@syukaworld", "슈카월드 - 경제 이슈 분석"),
    "체인지그라운드": ("@changeground2030", "체인지그라운드 - 경제/투자"),
    "박곰희TV": ("@Gomheetv", "박곰희TV - 재테크/자산관리"),
    "에코노미스트": ("@economistkorea", "이코노미스트 - 경제뉴스"),
    "한국경제TV": ("@WOWTV", "한국경제TV - 경제뉴스"),
    "머니투데이": ("@maboroshi_news", "머니투데이 - 경제뉴스"),
}


def get_channel_presets() -> dict[str, dict[str, str]]:
    """Get list of preset Korean investment channels."""
    return {
        name: {"channel_id": cid, "description": desc}
        for name, (cid, desc) in KOREAN_INVESTMENT_CHANNELS.items()
    }


# =============================================================================
# Video ID Extraction
# =============================================================================


def extract_video_id(url_or_id: str) -> str | None:
    """Extract video ID from YouTube URL or return as-is if already an ID.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - VIDEO_ID (11 characters)

    Args:
        url_or_id: YouTube URL or video ID.

    Returns:
        Video ID or None if invalid.
    """
    # Already a video ID (11 characters, alphanumeric + _ -)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id

    # Parse URL
    try:
        parsed = urlparse(url_or_id)

        # youtube.com/watch?v=ID
        if "youtube.com" in parsed.netloc:
            if parsed.path == "/watch":
                query = parse_qs(parsed.query)
                if "v" in query:
                    return query["v"][0]
            # youtube.com/embed/ID
            elif "/embed/" in parsed.path:
                return parsed.path.split("/embed/")[1].split("?")[0]
            # youtube.com/v/ID
            elif "/v/" in parsed.path:
                return parsed.path.split("/v/")[1].split("?")[0]

        # youtu.be/ID
        elif "youtu.be" in parsed.netloc:
            return parsed.path[1:].split("?")[0]

    except Exception:
        pass

    return None


def extract_channel_id(url_or_id: str) -> tuple[str | None, str]:
    """Extract channel ID from YouTube URL or handle/name.

    Args:
        url_or_id: Channel URL, handle (@name), or channel ID.

    Returns:
        Tuple of (channel_id, input_type).
        input_type: "id", "handle", "custom", "unknown"
    """
    url_or_id = url_or_id.strip()

    # Check preset channels first
    if url_or_id in KOREAN_INVESTMENT_CHANNELS:
        return KOREAN_INVESTMENT_CHANNELS[url_or_id][0], "preset"

    # Handle format: @channelname
    if url_or_id.startswith("@"):
        return url_or_id, "handle"

    # Already a channel ID (UC + 22 characters)
    if re.match(r"^UC[a-zA-Z0-9_-]{22}$", url_or_id):
        return url_or_id, "id"

    # Parse URL
    try:
        parsed = urlparse(url_or_id)

        if "youtube.com" in parsed.netloc:
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) >= 2:
                if path_parts[0] == "channel":
                    # youtube.com/channel/CHANNEL_ID
                    return path_parts[1], "id"
                elif path_parts[0] == "c":
                    # youtube.com/c/customname
                    return path_parts[1], "custom"
                elif path_parts[0] == "user":
                    # youtube.com/user/username
                    return path_parts[1], "user"
                elif path_parts[0].startswith("@"):
                    # youtube.com/@handle
                    return path_parts[0], "handle"

    except Exception:
        pass

    return url_or_id, "unknown"


# =============================================================================
# Transcript Extraction
# =============================================================================


async def get_transcript(
    video_url_or_id: str,
    languages: list[str] | None = None,
) -> YouTubeTranscript | None:
    """Get transcript from a YouTube video.

    Args:
        video_url_or_id: YouTube video URL or ID.
        languages: Preferred languages in order. Default: ["ko", "en"]

    Returns:
        YouTubeTranscript object or None if not available.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise ImportError(
            "youtube-transcript-api is required. "
            "Install with: pip install youtube-transcript-api"
        )

    video_id = extract_video_id(video_url_or_id)
    if not video_id:
        print(f"Invalid video URL/ID: {video_url_or_id}")
        return None

    languages = languages or ["ko", "en"]

    try:
        # Get video info first
        video_info = await get_video_info(video_id)

        # Get transcript (run in thread pool)
        def _get_transcript():
            try:
                api = YouTubeTranscriptApi()

                # Try to fetch with preferred languages first
                for lang in languages:
                    try:
                        result = api.fetch(video_id, languages=[lang])
                        # Convert to list of dicts
                        segments = [
                            {"text": seg.text, "start": seg.start, "duration": seg.duration}
                            for seg in result
                        ]
                        return segments, lang
                    except Exception:
                        continue

                # Fallback: try to get any available transcript
                try:
                    transcript_list = api.list(video_id)
                    # Get first available transcript
                    for t in transcript_list:
                        result = t.fetch()
                        segments = [
                            {"text": seg.text, "start": seg.start, "duration": seg.duration}
                            for seg in result
                        ]
                        return segments, t.language_code
                except Exception:
                    pass

                return None, None

            except Exception as e:
                print(f"Transcript error: {e}")
                return None, None

        result = await asyncio.to_thread(_get_transcript)
        segments, language = result

        if not segments:
            return None

        # Combine segments into full text
        full_text = " ".join(seg["text"] for seg in segments)

        # Calculate total duration
        duration = 0.0
        if segments:
            last_seg = segments[-1]
            duration = last_seg.get("start", 0) + last_seg.get("duration", 0)

        return YouTubeTranscript(
            video_id=video_id,
            title=video_info.get("title", "Unknown"),
            channel_name=video_info.get("channel_name", "Unknown"),
            language=language or "unknown",
            text=full_text,
            segments=segments,
            duration_seconds=duration,
        )

    except Exception as e:
        print(f"Error getting transcript for {video_id}: {e}")
        return None


async def get_video_info(video_id: str) -> dict[str, Any]:
    """Get basic video info via oembed (no API key needed).

    Args:
        video_id: YouTube video ID.

    Returns:
        Dictionary with video info.
    """
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", ""),
                    "channel_name": data.get("author_name", ""),
                    "channel_url": data.get("author_url", ""),
                    "thumbnail_url": data.get("thumbnail_url", ""),
                }
    except Exception as e:
        print(f"Error getting video info: {e}")

    return {"title": "", "channel_name": ""}


# =============================================================================
# Channel Videos via RSS
# =============================================================================


async def get_channel_videos(
    channel_identifier: str,
    max_results: int = 15,
) -> list[YouTubeVideo]:
    """Get recent videos from a YouTube channel via RSS feed.

    Args:
        channel_identifier: Channel ID, handle (@name), preset name, or URL.
        max_results: Maximum number of videos to return.

    Returns:
        List of YouTubeVideo objects.
    """
    channel_id, id_type = extract_channel_id(channel_identifier)

    if not channel_id:
        print(f"Could not extract channel ID from: {channel_identifier}")
        return []

    # For handles and presets (which now use handles), resolve to channel ID
    if id_type in ("handle", "preset"):
        resolved_id = await _resolve_handle_to_channel_id(channel_id)
        if resolved_id:
            channel_id = resolved_id
        else:
            print(f"Could not resolve handle: {channel_id}")
            return []

    # Build RSS URL
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(rss_url, timeout=10.0)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Namespace
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/",
            }

            videos: list[YouTubeVideo] = []

            # Get channel name from feed title
            channel_name = ""
            title_elem = root.find("atom:title", ns)
            if title_elem is not None and title_elem.text:
                channel_name = title_elem.text

            # Parse entries
            entries = root.findall("atom:entry", ns)

            for entry in entries[:max_results]:
                video_id_elem = entry.find("yt:videoId", ns)
                title_elem = entry.find("atom:title", ns)
                published_elem = entry.find("atom:published", ns)

                # Media group for description and thumbnail
                media_group = entry.find("media:group", ns)
                description = ""
                thumbnail_url = ""

                if media_group is not None:
                    desc_elem = media_group.find("media:description", ns)
                    if desc_elem is not None and desc_elem.text:
                        description = desc_elem.text

                    thumb_elem = media_group.find("media:thumbnail", ns)
                    if thumb_elem is not None:
                        thumbnail_url = thumb_elem.get("url", "")

                if video_id_elem is not None and video_id_elem.text:
                    videos.append(
                        YouTubeVideo(
                            video_id=video_id_elem.text,
                            title=title_elem.text if title_elem is not None else "",
                            channel_name=channel_name,
                            channel_id=channel_id,
                            published=published_elem.text if published_elem is not None else None,
                            description=description[:500] if description else None,
                            thumbnail_url=thumbnail_url,
                        )
                    )

            return videos

    except Exception as e:
        print(f"Error getting channel videos: {e}")
        return []


async def _resolve_handle_to_channel_id(handle: str) -> str | None:
    """Resolve a YouTube handle (@name) to channel ID.

    Args:
        handle: YouTube handle (with or without @).

    Returns:
        Channel ID or None if not found.
    """
    if not handle.startswith("@"):
        handle = f"@{handle}"

    url = f"https://www.youtube.com/{handle}"

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, timeout=10.0)

            # Look for channel ID in the page
            content = response.text

            # Find channel ID pattern
            match = re.search(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"', content)
            if match:
                return match.group(1)

            # Alternative pattern
            match = re.search(r'channel_id=([^"&]+)', content)
            if match:
                return match.group(1)

    except Exception as e:
        print(f"Error resolving handle {handle}: {e}")

    return None


# =============================================================================
# RAG Integration
# =============================================================================


async def get_transcript_and_store_to_rag(
    video_url_or_id: str,
    kb_name: str = "youtube",
    languages: list[str] | None = None,
) -> dict[str, Any]:
    """Get video transcript and store in RAG knowledge base.

    Args:
        video_url_or_id: YouTube video URL or ID.
        kb_name: Knowledge base name.
        languages: Preferred languages.

    Returns:
        Result dictionary.
    """
    from src.services.rag import get_rag_service
    from src.services.rag.types import Chunk

    transcript = await get_transcript(video_url_or_id, languages)

    if not transcript:
        return {
            "success": False,
            "error": "Could not get transcript. Video may not have captions.",
        }

    # Create metadata for all chunks
    base_metadata = {
        "video_id": transcript.video_id,
        "title": transcript.title,
        "channel_name": transcript.channel_name,
        "language": transcript.language,
        "duration_seconds": transcript.duration_seconds,
        "url": f"https://www.youtube.com/watch?v={transcript.video_id}",
        "source": f"youtube:{transcript.video_id}",
    }

    # Split text into chunks (max ~6000 chars to stay under token limit)
    full_text = transcript.to_text()
    chunk_size = 6000
    chunk_overlap = 200

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(full_text):
        end = min(start + chunk_size, len(full_text))

        # Try to break at sentence boundary
        if end < len(full_text):
            # Look for sentence ending within last 200 chars
            for i in range(end, max(start + chunk_size - 200, start), -1):
                if full_text[i] in '.!?\n':
                    end = i + 1
                    break

        chunk_text = full_text[start:end].strip()
        if chunk_text:
            chunks.append(Chunk(
                content=chunk_text,
                chunk_type="youtube_transcript",
                metadata={
                    **base_metadata,
                    "chunk_index": chunk_idx,
                },
            ))
            chunk_idx += 1

        start = end - chunk_overlap if end < len(full_text) else end

    # Store in RAG
    service = get_rag_service()
    retriever = service._get_or_create_retriever(kb_name)
    await retriever.add_chunks(chunks)

    return {
        "success": True,
        "video_id": transcript.video_id,
        "title": transcript.title,
        "channel_name": transcript.channel_name,
        "language": transcript.language,
        "duration_minutes": round(transcript.duration_seconds / 60, 1),
        "text_length": len(transcript.text),
        "chunks_created": len(chunks),
        "kb_name": kb_name,
        "stored": True,
    }


async def get_channel_videos_and_store_to_rag(
    channel_identifier: str,
    kb_name: str = "youtube",
    max_videos: int = 5,
    languages: list[str] | None = None,
) -> dict[str, Any]:
    """Get recent videos from channel and store transcripts in RAG.

    Args:
        channel_identifier: Channel ID, handle, or preset name.
        kb_name: Knowledge base name.
        max_videos: Maximum videos to process.
        languages: Preferred languages.

    Returns:
        Result dictionary with processed videos.
    """
    videos = await get_channel_videos(channel_identifier, max_results=max_videos)

    if not videos:
        return {
            "success": False,
            "error": "Could not get channel videos.",
        }

    results: list[dict[str, Any]] = []

    for video in videos:
        result = await get_transcript_and_store_to_rag(
            video.video_id,
            kb_name=kb_name,
            languages=languages,
        )
        results.append({
            "video_id": video.video_id,
            "title": video.title,
            **result,
        })

    successful = sum(1 for r in results if r.get("success", False))

    return {
        "success": True,
        "channel": channel_identifier,
        "total_videos": len(videos),
        "processed": successful,
        "failed": len(videos) - successful,
        "kb_name": kb_name,
        "results": results,
    }


# =============================================================================
# Tool Definitions for Agent
# =============================================================================


YOUTUBE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_youtube_transcript",
            "description": (
                "Get the transcript (subtitles/captions) from a YouTube video. "
                "Use this to analyze video content, extract insights from "
                "investment/finance YouTube videos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "YouTube video URL or video ID.",
                    },
                    "store_to_rag": {
                        "type": "boolean",
                        "description": "Whether to store transcript in RAG knowledge base.",
                        "default": False,
                    },
                    "kb_name": {
                        "type": "string",
                        "description": "Knowledge base name if storing to RAG.",
                        "default": "youtube",
                    },
                },
                "required": ["video_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_channel_recent_videos",
            "description": (
                "Get recent videos from a YouTube channel. "
                "Supports preset Korean investment channels: "
                "삼프로TV, 슈카월드, 신사임당, 부읽남, 월급쟁이부자들TV, etc. "
                "Can also use channel ID, handle (@name), or URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": (
                            "Channel identifier. Can be: preset name (삼프로TV), "
                            "handle (@3protv), channel ID, or channel URL."
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of videos to return.",
                        "default": 10,
                    },
                },
                "required": ["channel"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_investment_channels",
            "description": (
                "List preset Korean investment YouTube channels available for analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


async def execute_youtube_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Execute a YouTube tool by name.

    Args:
        tool_name: Name of the tool.
        arguments: Tool arguments.

    Returns:
        Tool result.
    """
    if tool_name == "get_youtube_transcript":
        video_url = arguments.get("video_url", "")
        store_to_rag = arguments.get("store_to_rag", False)
        kb_name = arguments.get("kb_name", "youtube")

        if store_to_rag:
            return await get_transcript_and_store_to_rag(
                video_url, kb_name=kb_name
            )
        else:
            transcript = await get_transcript(video_url)
            if transcript:
                return {
                    "success": True,
                    **transcript.to_dict(),
                    "text_preview": transcript.text[:2000] + "..." if len(transcript.text) > 2000 else transcript.text,
                }
            else:
                return {
                    "success": False,
                    "error": "Could not get transcript.",
                }

    elif tool_name == "get_channel_recent_videos":
        channel = arguments.get("channel", "")
        max_results = arguments.get("max_results", 10)

        videos = await get_channel_videos(channel, max_results)
        return {
            "success": True,
            "channel": channel,
            "video_count": len(videos),
            "videos": [v.to_dict() for v in videos],
        }

    elif tool_name == "list_investment_channels":
        return {
            "success": True,
            "channels": get_channel_presets(),
        }

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }
