from urllib.parse import urlparse

import pytest

from devcc.models import ConnectionURL


def test_connection_url_from_string_ssh():
    url = "ssh://hostname:22"
    conn = ConnectionURL.from_string(url)
    assert conn.scheme == "ssh://"
    assert conn.host == "hostname"
    assert conn.port == 22
    assert conn.path is None


def test_connection_url_from_string_tcp():
    url = "tcp://localhost:8080"
    conn = ConnectionURL.from_string(url)
    assert conn.scheme == "tcp://"
    assert conn.host == "localhost"
    assert conn.port == 8080
    assert conn.path is None


def test_connection_url_from_string_unix():
    url = "unix:///tmp/socket.sock"
    conn = ConnectionURL.from_string(url)
    assert conn.scheme == "unix://"
    assert conn.host is None
    assert conn.port is None
    assert conn.path == "/tmp/socket.sock"


def test_connection_url_from_string_invalid_scheme():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ftp://hostname:22")
    assert "Invalid URL scheme: ftp://" in str(exc_info.value)


def test_connection_url_from_string_empty_host():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh:// :22")
    assert "host is required for ssh:// and tcp:// schemes" in str(exc_info.value)


def test_connection_url_from_string_empty_port():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh://hostname:")
    assert "port is required for ssh:// and tcp:// schemes" in str(exc_info.value)


def test_connection_url_from_string_invalid_port_low():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh://hostname:0")
    assert "port must be between 1 and 65535" in str(exc_info.value)


def test_connection_url_from_string_invalid_port_high():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh://hostname:65536")
    assert "port must be between 1 and 65535" in str(exc_info.value)


def test_connection_url_from_string_invalid_port_format():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh://hostname:abc")
    assert "port must be an integer between 1 and 65535" in str(exc_info.value)


def test_connection_url_from_string_unix_missing_path():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("unix://")
    assert "path is required for unix:// scheme" in str(exc_info.value)


def test_connection_url_from_string_unix_with_host():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("unix://hostname/tmp/socket.sock")
    assert "host and port should not be set for unix:// scheme" in str(exc_info.value)


def test_connection_url_from_string_unix_with_port():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("unix://:22/tmp/socket.sock")
    assert "host and port should not be set for unix:// scheme" in str(exc_info.value)


def test_connection_url_from_string_ssh_with_path():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("ssh://hostname:22/path")
    assert "path should not be set for ssh:// and tcp:// schemes" in str(exc_info.value)


def test_connection_url_from_string_tcp_with_path():
    with pytest.raises(ValueError) as exc_info:
        ConnectionURL.from_string("tcp://localhost:8080/path")
    assert "path should not be set for ssh:// and tcp:// schemes" in str(exc_info.value) 