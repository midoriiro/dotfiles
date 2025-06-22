import pytest

from compose.models import ConnectionURL


def test_connection_url_to_string():
    """Test that ConnectionURL correctly formats a valid URL."""
    url = ConnectionURL.from_string("tcp://localhost:2375")
    assert url.to_string() == "tcp://localhost:2375" 