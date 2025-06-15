from urllib.parse import urlparse

import pytest

from devcc.models import ConnectionURL


def test_connection_url_validation_scheme():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL(scheme="invalid://")
    assert "Input should be 'ssh://', 'tcp://' or 'unix://'" in str(exc_info.value)


def test_connection_url_roundtrip_ssh():
    original_url = "ssh://hostname:22"
    conn = ConnectionURL.from_string(original_url)
    assert conn.to_string() == original_url


def test_connection_url_roundtrip_tcp():
    original_url = "tcp://localhost:8080"
    conn = ConnectionURL.from_string(original_url)
    assert conn.to_string() == original_url


def test_connection_url_roundtrip_unix():
    original_url = "unix:///tmp/socket.sock"
    conn = ConnectionURL.from_string(original_url)
    assert conn.to_string() == original_url 