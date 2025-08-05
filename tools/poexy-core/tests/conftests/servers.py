import shutil
import socket
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from typing import Callable, Generator

import pytest

from poexy_core.utils import subprocess_rt


def wait_for_port(host, port, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    raise TimeoutError(f"Port {port} on {host} did not open in {timeout} seconds")


def start_http_server(directory, port, log_info) -> Generator[str, None, None]:
    class HttpRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(directory=directory, *args, **kwargs)

    try:
        log_info(f"Starting HTTP server at {directory}")
        handler = HttpRequestHandler
        httpd = HTTPServer(("localhost", port), handler, False)
        httpd.allow_reuse_address = True
        httpd.allow_reuse_port = True
        httpd.server_bind()
        httpd.server_activate()
        thread = Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        log_info(f"HTTP server started at {httpd.server_address}")
        yield f"http://localhost:{port}"
        log_info("Stopping HTTP server")
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=0.5)
        log_info("HTTP server stopped")
    except Exception as e:
        log_info(f"Error in HTTP server: {e}")
        raise e


@pytest.fixture()
def serve_library_archive(
    tmp_path, samples_path, log_info_section, log_info
) -> Callable[[], None]:
    def _serve_library_archive() -> None:
        log_info_section("Serving library archive")
        library_path = samples_path / "library" / "library-1.0.0-py3-none-any.whl"
        shutil.copy(library_path, tmp_path)
        next(start_http_server(tmp_path, 8000, log_info))
        wait_for_port("localhost", 8000, timeout=30)

    return _serve_library_archive


def start_git_daemon(directory, port, log_info) -> Generator[None, None, None]:
    def run_daemon() -> None:
        subprocess_rt.run(
            [
                "git",
                "daemon",
                "--verbose",
                "--export-all",
                "--reuseaddr",
                "--listen=localhost",
                f"--port={port}",
                f"--base-path={directory}",
            ],
            printer=log_info,
        )

    thread = Thread(target=run_daemon, daemon=True)
    thread.start()
    log_info(f"GIT server started at localhost:{port}")
    yield
    log_info("Stopping GIT server")
    thread.join(timeout=0.5)
    log_info("GIT server stopped")


@pytest.fixture()
def serve_library_vcs(
    tmp_path, samples_path, log_info_section, log_info
) -> Callable[[], None]:
    def _serve_library_vcs() -> None:
        log_info_section("Serving library vcs")
        library_path = samples_path / "library"
        shutil.copytree(library_path, tmp_path, dirs_exist_ok=True)
        subprocess_rt.run(["git", "init"], printer=log_info, cwd=tmp_path)
        subprocess_rt.run(
            ["git", "branch", "-m", "main"], printer=log_info, cwd=tmp_path
        )
        subprocess_rt.run(["git", "add", "-A"], printer=log_info, cwd=tmp_path)
        subprocess_rt.run(
            ["git", "commit", "-m", "Initial commit"], printer=log_info, cwd=tmp_path
        )
        next(start_git_daemon(tmp_path, 8001, log_info))
        wait_for_port("localhost", 8001, timeout=30)

    return _serve_library_vcs
