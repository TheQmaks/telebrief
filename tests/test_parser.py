"""Tests for parser module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from telebrief import TelegramParser
from telebrief.models import ChannelInfo, Post
from telebrief.utils import Config


class TestTelegramParser:
    """Tests for TelegramParser class."""

    @pytest.fixture
    def parser(self):
        """Creates a parser instance for tests."""
        config = Config()
        config.network.use_proxy = False
        return TelegramParser(config)

    @pytest.fixture
    def mock_response(self):
        """Creates a mock HTTP response."""
        response = Mock()
        response.status_code = 200
        response.text = """
        <div class="tgme_page_title">Test Channel</div>
        <div class="tgme_page_extra">1.5K subscribers</div>
        <div class="tgme_page_description">Test description</div>
        """
        return response

    def test_parse_number_with_suffix(self, parser):
        """Test parsing numbers with suffixes."""
        assert parser._parse_number_with_suffix("1.5K") == 1500
        assert parser._parse_number_with_suffix("2M") == 2000000
        assert parser._parse_number_with_suffix("1,234") == 1234
        assert parser._parse_number_with_suffix("500") == 500
        assert parser._parse_number_with_suffix("") == 0

    @patch('telebrief.core.parser.TelegramParser._make_request')
    def test_get_channel_info(self, mock_request, parser, mock_response):
        """Test getting channel information."""
        mock_request.return_value = mock_response

        info = parser._get_channel_info("testchannel")

        assert info.channel == "testchannel"
        assert info.name == "Test Channel"
        assert info.subscribers == 1500
        assert info.description == "Test description"

    def test_html_to_markdown(self, parser):
        """Test HTML to Markdown conversion."""
        html = '<b>Bold</b> <i>italic</i> <a href="http://example.com">link</a>'
        markdown = parser._html_to_markdown(html)
        # html2text uses _ for italics and no <> wrapping with current settings
        assert markdown == '**Bold** _italic_ [link](http://example.com)'

    def test_validate_channel_name(self, parser):
        """Test channel name validation."""
        with pytest.raises(ValueError, match="Invalid channel name"):
            parser.parse_channel("", days=1)

        with pytest.raises(ValueError, match="Invalid channel name"):
            parser.parse_channel("ab", days=1)  # Too short

        with pytest.raises(ValueError, match="Invalid channel name"):
            parser.parse_channel("invalid channel", days=1)  # Contains space

    def test_validate_days_parameter(self, parser):
        """Test days parameter validation."""
        with pytest.raises(ValueError, match="Number of days must be positive"):
            parser.parse_channel("validchannel", days=-1)

    @patch('telebrief.core.parser.TelegramParser._make_request')
    @patch('telebrief.core.parser.TelegramParser._get_channel_info')
    @patch('telebrief.core.parser.TelegramParser._get_posts')
    def test_parse_channel_success(self, mock_posts, mock_info, mock_request, parser):
        """Test successful channel parsing."""
        mock_info.return_value = ChannelInfo(
            channel="testchannel",
            name="Test Channel",
            description="Test",
            subscribers=1000
        )

        posts = [
            Post(
                post_id=1,
                views=1000,
                date=datetime.now(),
                author="testchannel",
                text="Test post",
            )
        ]
        mock_posts.return_value = (posts, 1)  # Return tuple (posts, latest_post_id)

        channel = parser.parse_channel("testchannel", days=7)

        assert channel.info.channel == "testchannel"
        assert len(channel.posts) == 1
        assert channel.posts[0].views == 1000
