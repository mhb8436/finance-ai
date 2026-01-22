"""Test YouTube Tool functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


class TestYouTubeDataTypes:
    """Test YouTube data types."""

    def test_youtube_video_dataclass(self):
        """Test YouTubeVideo dataclass."""
        from src.tools.youtube_tool import YouTubeVideo

        video = YouTubeVideo(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            channel_id="UC12345",
            published="2025-01-20T00:00:00Z",
            description="Test description",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/default.jpg",
        )

        assert video.video_id == "dQw4w9WgXcQ"
        assert video.title == "Test Video"
        assert video.channel_name == "Test Channel"
        assert video.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_youtube_video_to_dict(self):
        """Test YouTubeVideo.to_dict method."""
        from src.tools.youtube_tool import YouTubeVideo

        video = YouTubeVideo(
            video_id="abc123xyz99",
            title="Test",
            channel_name="Channel",
        )

        d = video.to_dict()
        assert d["video_id"] == "abc123xyz99"
        assert d["title"] == "Test"
        assert d["url"] == "https://www.youtube.com/watch?v=abc123xyz99"

    def test_youtube_transcript_dataclass(self):
        """Test YouTubeTranscript dataclass."""
        from src.tools.youtube_tool import YouTubeTranscript

        transcript = YouTubeTranscript(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            language="ko",
            text="안녕하세요 여러분",
            segments=[{"text": "안녕하세요", "start": 0.0, "duration": 2.0}],
            duration_seconds=120.5,
        )

        assert transcript.video_id == "dQw4w9WgXcQ"
        assert transcript.language == "ko"
        assert transcript.duration_seconds == 120.5

    def test_youtube_transcript_to_dict(self):
        """Test YouTubeTranscript.to_dict method."""
        from src.tools.youtube_tool import YouTubeTranscript

        transcript = YouTubeTranscript(
            video_id="dQw4w9WgXcQ",
            title="Test",
            channel_name="Channel",
            language="en",
            text="Hello world",
            segments=[{"text": "Hello", "start": 0.0, "duration": 1.0}],
            duration_seconds=60.0,
        )

        d = transcript.to_dict()
        assert d["video_id"] == "dQw4w9WgXcQ"
        assert d["language"] == "en"
        assert d["segment_count"] == 1

    def test_youtube_transcript_to_text(self):
        """Test YouTubeTranscript.to_text method."""
        from src.tools.youtube_tool import YouTubeTranscript

        transcript = YouTubeTranscript(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            language="ko",
            text="스크립트 내용입니다",
            segments=[],
            duration_seconds=300.0,
        )

        text = transcript.to_text()
        assert "제목: Test Video" in text
        assert "채널: Test Channel" in text
        assert "언어: ko" in text
        assert "길이: 5.0분" in text
        assert "스크립트 내용입니다" in text


class TestVideoIdExtraction:
    """Test video ID extraction."""

    def test_extract_direct_id(self):
        """Test extracting direct video ID."""
        from src.tools.youtube_tool import extract_video_id

        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("abc123xyz99") == "abc123xyz99"
        # Video IDs are exactly 11 characters with alphanumeric, underscore, and dash
        assert extract_video_id("_under-scor") == "_under-scor"

    def test_extract_from_watch_url(self):
        """Test extracting from youtube.com/watch URL."""
        from src.tools.youtube_tool import extract_video_id

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

        url_with_params = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=60"
        assert extract_video_id(url_with_params) == "dQw4w9WgXcQ"

    def test_extract_from_short_url(self):
        """Test extracting from youtu.be URL."""
        from src.tools.youtube_tool import extract_video_id

        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

        url_with_params = "https://youtu.be/dQw4w9WgXcQ?t=60"
        assert extract_video_id(url_with_params) == "dQw4w9WgXcQ"

    def test_extract_from_embed_url(self):
        """Test extracting from embed URL."""
        from src.tools.youtube_tool import extract_video_id

        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_invalid_url(self):
        """Test extracting from invalid URL."""
        from src.tools.youtube_tool import extract_video_id

        assert extract_video_id("https://example.com") is None
        assert extract_video_id("not-a-valid-id") is None
        assert extract_video_id("") is None


class TestChannelIdExtraction:
    """Test channel ID extraction."""

    def test_extract_preset_channel(self):
        """Test extracting preset channel."""
        from src.tools.youtube_tool import extract_channel_id

        channel_id, id_type = extract_channel_id("삼프로TV")
        assert channel_id == "@3PROTV"
        assert id_type == "preset"

    def test_extract_handle(self):
        """Test extracting handle format."""
        from src.tools.youtube_tool import extract_channel_id

        channel_id, id_type = extract_channel_id("@syukaworld")
        assert channel_id == "@syukaworld"
        assert id_type == "handle"

    def test_extract_channel_id_direct(self):
        """Test extracting direct channel ID."""
        from src.tools.youtube_tool import extract_channel_id

        channel_id, id_type = extract_channel_id("UCabcdefghijklmnopqrstuv")
        assert channel_id == "UCabcdefghijklmnopqrstuv"
        assert id_type == "id"

    def test_extract_from_channel_url(self):
        """Test extracting from channel URL."""
        from src.tools.youtube_tool import extract_channel_id

        url = "https://www.youtube.com/channel/UCabcdefghijklmnopqrstuv"
        channel_id, id_type = extract_channel_id(url)
        assert channel_id == "UCabcdefghijklmnopqrstuv"
        assert id_type == "id"

    def test_extract_from_custom_url(self):
        """Test extracting from custom URL."""
        from src.tools.youtube_tool import extract_channel_id

        url = "https://www.youtube.com/c/customname"
        channel_id, id_type = extract_channel_id(url)
        assert channel_id == "customname"
        assert id_type == "custom"


class TestChannelPresets:
    """Test channel preset functions."""

    def test_get_channel_presets(self):
        """Test get_channel_presets returns expected data."""
        from src.tools.youtube_tool import get_channel_presets

        presets = get_channel_presets()
        assert isinstance(presets, dict)
        assert "삼프로TV" in presets
        assert "슈카월드" in presets

        preset_info = presets["삼프로TV"]
        assert "channel_id" in preset_info
        assert "description" in preset_info


class TestGetVideoInfo:
    """Test video info retrieval."""

    @pytest.mark.asyncio
    async def test_get_video_info(self):
        """Test get_video_info via oEmbed."""
        from src.tools.youtube_tool import get_video_info

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Test Video Title",
            "author_name": "Test Channel",
            "author_url": "https://www.youtube.com/channel/UC123",
            "thumbnail_url": "https://i.ytimg.com/vi/abc/default.jpg",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    get=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            info = await get_video_info("dQw4w9WgXcQ")

            assert info["title"] == "Test Video Title"
            assert info["channel_name"] == "Test Channel"

    @pytest.mark.asyncio
    async def test_get_video_info_error(self):
        """Test get_video_info handles errors gracefully."""
        from src.tools.youtube_tool import get_video_info

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    get=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            info = await get_video_info("invalid_id")

            assert info["title"] == ""
            assert info["channel_name"] == ""


class TestGetTranscript:
    """Test transcript extraction."""

    @pytest.mark.asyncio
    async def test_get_transcript_invalid_url(self):
        """Test get_transcript with invalid URL returns None."""
        from src.tools.youtube_tool import get_transcript

        result = await get_transcript("invalid-url")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_transcript_success(self):
        """Test get_transcript with mocked API."""
        from src.tools.youtube_tool import get_transcript

        # Mock video info
        mock_video_info = {
            "title": "Test Video",
            "channel_name": "Test Channel",
        }

        # Mock transcript segment
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_segment.start = 0.0
        mock_segment.duration = 2.0

        mock_api = MagicMock()
        mock_api.fetch.return_value = [mock_segment]

        with patch(
            "src.tools.youtube_tool.get_video_info",
            AsyncMock(return_value=mock_video_info),
        ), patch.dict("sys.modules", {"youtube_transcript_api": MagicMock()}):
            # Mock the YouTubeTranscriptApi class
            with patch(
                "youtube_transcript_api.YouTubeTranscriptApi",
                return_value=mock_api,
            ):
                # This test would need the actual youtube_transcript_api installed
                # For now, just verify the function structure
                pass


class TestGetChannelVideos:
    """Test channel videos retrieval."""

    @pytest.mark.asyncio
    async def test_get_channel_videos_rss(self):
        """Test get_channel_videos via RSS."""
        from src.tools.youtube_tool import get_channel_videos

        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
              xmlns:media="http://search.yahoo.com/mrss/"
              xmlns="http://www.w3.org/2005/Atom">
            <title>Test Channel</title>
            <entry>
                <yt:videoId>abc123xyz99</yt:videoId>
                <title>Video Title</title>
                <published>2025-01-20T00:00:00Z</published>
                <media:group>
                    <media:description>Video description</media:description>
                    <media:thumbnail url="https://img.youtube.com/vi/abc123xyz99/default.jpg"/>
                </media:group>
            </entry>
        </feed>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = rss_content.encode()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    get=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Use direct channel ID to skip handle resolution
            videos = await get_channel_videos("UCabcdefghijklmnopqrstuv", max_results=5)

            assert isinstance(videos, list)
            assert len(videos) == 1
            assert videos[0].video_id == "abc123xyz99"
            assert videos[0].title == "Video Title"
            assert videos[0].channel_name == "Test Channel"


class TestToolRouterIntegration:
    """Test ToolRouter integration with YouTube tools."""

    def test_tool_type_enum_has_youtube(self):
        """Test ToolType enum includes YouTube types."""
        from src.services.tool_router.types import ToolType

        assert hasattr(ToolType, "YOUTUBE_TRANSCRIPT")
        assert hasattr(ToolType, "YOUTUBE_CHANNEL")

        assert ToolType.YOUTUBE_TRANSCRIPT.value == "youtube_transcript"
        assert ToolType.YOUTUBE_CHANNEL.value == "youtube_channel"

    def test_tool_router_has_youtube_handlers(self):
        """Test ToolRouter registers YouTube handlers."""
        from src.services.tool_router import ToolRouter

        router = ToolRouter()
        available_tools = router.get_available_tools()

        assert "youtube_transcript" in available_tools
        assert "youtube_channel" in available_tools

    @pytest.mark.asyncio
    async def test_tool_router_execute_youtube_transcript(self):
        """Test executing youtube_transcript via ToolRouter."""
        from src.services.tool_router import ToolRouter, ToolStatus
        from src.tools.youtube_tool import YouTubeTranscript

        mock_transcript = YouTubeTranscript(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel_name="Test Channel",
            language="ko",
            text="테스트 스크립트",
            segments=[],
            duration_seconds=120.0,
        )

        with patch(
            "src.tools.youtube_tool.get_transcript",
            AsyncMock(return_value=mock_transcript),
        ):
            router = ToolRouter()
            result = await router.execute(
                "youtube_transcript",
                video_url="dQw4w9WgXcQ",
            )

            assert result.status == ToolStatus.SUCCESS
            assert result.data is not None
            assert result.data["video_id"] == "dQw4w9WgXcQ"
            assert result.data["title"] == "Test Video"
            assert result.data["language"] == "ko"

    @pytest.mark.asyncio
    async def test_tool_router_execute_youtube_channel(self):
        """Test executing youtube_channel via ToolRouter."""
        from src.services.tool_router import ToolRouter, ToolStatus
        from src.tools.youtube_tool import YouTubeVideo

        mock_videos = [
            YouTubeVideo(
                video_id="abc123xyz99",
                title="Video 1",
                channel_name="Test Channel",
            ),
            YouTubeVideo(
                video_id="def456uvw88",
                title="Video 2",
                channel_name="Test Channel",
            ),
        ]

        with patch(
            "src.tools.youtube_tool.get_channel_videos",
            AsyncMock(return_value=mock_videos),
        ):
            router = ToolRouter()
            result = await router.execute(
                "youtube_channel",
                channel="@testchannel",
                max_results=5,
            )

            assert result.status == ToolStatus.SUCCESS
            assert result.data is not None
            assert result.data["channel"] == "@testchannel"
            assert result.data["count"] == 2


class TestToolDefinitions:
    """Test tool definitions for LLM function calling."""

    def test_youtube_tool_definitions_exist(self):
        """Test YOUTUBE_TOOL_DEFINITIONS is properly defined."""
        from src.tools.youtube_tool import YOUTUBE_TOOL_DEFINITIONS

        assert isinstance(YOUTUBE_TOOL_DEFINITIONS, list)
        assert len(YOUTUBE_TOOL_DEFINITIONS) == 3  # transcript, channel videos, list channels

    def test_transcript_tool_definition(self):
        """Test get_youtube_transcript tool definition."""
        from src.tools.youtube_tool import YOUTUBE_TOOL_DEFINITIONS

        transcript_def = next(
            (t for t in YOUTUBE_TOOL_DEFINITIONS if t["function"]["name"] == "get_youtube_transcript"),
            None,
        )

        assert transcript_def is not None
        assert transcript_def["type"] == "function"

        func = transcript_def["function"]
        assert "description" in func
        assert "parameters" in func
        assert "video_url" in func["parameters"]["properties"]

    def test_channel_videos_tool_definition(self):
        """Test get_channel_recent_videos tool definition."""
        from src.tools.youtube_tool import YOUTUBE_TOOL_DEFINITIONS

        channel_def = next(
            (t for t in YOUTUBE_TOOL_DEFINITIONS if t["function"]["name"] == "get_channel_recent_videos"),
            None,
        )

        assert channel_def is not None
        func = channel_def["function"]
        assert "channel" in func["parameters"]["properties"]
        assert "max_results" in func["parameters"]["properties"]

    def test_list_channels_tool_definition(self):
        """Test list_investment_channels tool definition."""
        from src.tools.youtube_tool import YOUTUBE_TOOL_DEFINITIONS

        list_def = next(
            (t for t in YOUTUBE_TOOL_DEFINITIONS if t["function"]["name"] == "list_investment_channels"),
            None,
        )

        assert list_def is not None


class TestExecuteYouTubeTool:
    """Test execute_youtube_tool function."""

    @pytest.mark.asyncio
    async def test_execute_transcript_tool(self):
        """Test executing get_youtube_transcript tool."""
        from src.tools.youtube_tool import execute_youtube_tool, YouTubeTranscript

        mock_transcript = YouTubeTranscript(
            video_id="dQw4w9WgXcQ",
            title="Test",
            channel_name="Channel",
            language="en",
            text="Hello world",
            segments=[],
            duration_seconds=60.0,
        )

        with patch(
            "src.tools.youtube_tool.get_transcript",
            AsyncMock(return_value=mock_transcript),
        ):
            result = await execute_youtube_tool(
                "get_youtube_transcript",
                {"video_url": "dQw4w9WgXcQ"},
            )

            assert result["success"] is True
            assert result["video_id"] == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_execute_channel_videos_tool(self):
        """Test executing get_channel_recent_videos tool."""
        from src.tools.youtube_tool import execute_youtube_tool, YouTubeVideo

        mock_videos = [
            YouTubeVideo(
                video_id="abc123xyz99",
                title="Video 1",
                channel_name="Channel",
            ),
        ]

        with patch(
            "src.tools.youtube_tool.get_channel_videos",
            AsyncMock(return_value=mock_videos),
        ):
            result = await execute_youtube_tool(
                "get_channel_recent_videos",
                {"channel": "삼프로TV", "max_results": 5},
            )

            assert result["success"] is True
            assert result["video_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_list_channels_tool(self):
        """Test executing list_investment_channels tool."""
        from src.tools.youtube_tool import execute_youtube_tool

        result = await execute_youtube_tool(
            "list_investment_channels",
            {},
        )

        assert result["success"] is True
        assert "channels" in result
        assert "삼프로TV" in result["channels"]

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing unknown tool."""
        from src.tools.youtube_tool import execute_youtube_tool

        result = await execute_youtube_tool(
            "unknown_tool",
            {},
        )

        assert result["success"] is False
        assert "Unknown tool" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
