from urllib.parse import urlparse

import pytest

from devcc.models import ConnectionURL


def test_connection_url_validation_scheme():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL(scheme="invalid://")
    assert "Input should be 'ssh://', 'tcp://' or 'unix://'" in str(exc_info.value)


def test_connection_url_roundtrip_ssh(ssh_connection_url):
    original_url = "ssh://hostname:22"
    assert ssh_connection_url.to_string() == original_url


def test_connection_url_roundtrip_tcp(tcp_connection_url):
    original_url = "tcp://localhost:8080"
    assert tcp_connection_url.to_string() == original_url


def test_connection_url_roundtrip_unix(unix_connection_url):
    original_url = "unix:///tmp/socket.sock"
    assert unix_connection_url.to_string() == original_url 