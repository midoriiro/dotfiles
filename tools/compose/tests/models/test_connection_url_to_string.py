from urllib.parse import urlparse

import pytest

from compose.models import ConnectionURL


def test_connection_url_to_string_ssh(ssh_connection_url):
    assert ssh_connection_url.to_string() == "ssh://hostname:22"


def test_connection_url_to_string_tcp(tcp_connection_url):
    assert tcp_connection_url.to_string() == "tcp://localhost:8080"


def test_connection_url_to_string_unix(unix_connection_url):
    assert unix_connection_url.to_string() == "unix:///tmp/socket.sock"


def test_connection_url_to_string_empty_host():
    conn = ConnectionURL(scheme="ssh://", host=" ", port=22)
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "host cannot be empty" in str(exc_info.value)


def test_connection_url_to_string_invalid_port_low():
    conn = ConnectionURL(scheme="ssh://", host="hostname", port=0)
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "port must be between 1 and 65535" in str(exc_info.value)


def test_connection_url_to_string_invalid_port_high():
    conn = ConnectionURL(scheme="ssh://", host="hostname", port=65536)
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "port must be between 1 and 65535" in str(exc_info.value)


def test_connection_url_to_string_missing_host():
    conn = ConnectionURL(scheme="ssh://", port=22)
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "host is required for ssh:// and tcp:// schemes" in str(exc_info.value)


def test_connection_url_to_string_missing_port():
    conn = ConnectionURL(scheme="ssh://", host="hostname")
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "port is required for ssh:// and tcp:// schemes" in str(exc_info.value)


def test_connection_url_to_string_unix_missing_path():
    conn = ConnectionURL(scheme="unix://")
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "path is required for unix:// scheme" in str(exc_info.value)


def test_connection_url_to_string_unix_with_host():
    conn = ConnectionURL(scheme="unix://", host="hostname", path="/tmp/socket.sock")
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "host and port should not be set for unix:// scheme" in str(exc_info.value)


def test_connection_url_to_string_unix_with_port():
    conn = ConnectionURL(scheme="unix://", port=22, path="/tmp/socket.sock")
    with pytest.raises(ValueError) as exc_info:
        conn.to_string()
    assert "host and port should not be set for unix:// scheme" in str(exc_info.value)
