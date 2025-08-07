import os
import signal
import socket
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Callable, Optional, override

from poexy_core.utils import subprocess_rt


class BaseServer:
    def __init__(self, directory: Path, port: int, logger):
        self.directory = directory
        self.port = port
        self.logger = logger
        self._thread: Optional[Thread] = None

    def _target(self) -> Callable[[], object]:
        raise NotImplementedError("Not implemented")

    def start(self):
        if self._thread is not None:
            raise RuntimeError("Server is already running")
        target = self._target()
        self._thread = Thread(target=target, daemon=False)
        self._thread.start()

    def stop(self):
        if self._thread is None:
            raise RuntimeError("Server is not running")
        if not self._thread.is_alive():
            raise RuntimeError("Server is not running")
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            raise RuntimeError("Server is still running")
        self._thread = None

    def wait_for_connection(self, timeout=5.0):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection(("localhost", self.port), timeout=0.5):
                    return True
            except (OSError, ConnectionRefusedError):
                time.sleep(0.1)
        raise TimeoutError(
            f"Port {self.port} on localhost did not open in {timeout} seconds"
        )


class HttpServer(BaseServer):
    def __init__(self, directory: Path, port: int, logger):
        super().__init__(directory, port, logger)
        self.__httpd: Optional[HTTPServer] = None

    @override
    def _target(self) -> Callable[[], object]:
        directory = self.directory

        class HttpRequestHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(directory=directory, *args, **kwargs)

        self.logger(f"Starting HTTP server at {self.directory}")
        handler = HttpRequestHandler
        self.__httpd = HTTPServer(("localhost", self.port), handler, False)
        self.__httpd.allow_reuse_address = True
        self.__httpd.allow_reuse_port = True
        self.__httpd.server_bind()
        self.__httpd.server_activate()
        self.logger(f"HTTP server started at {self.__httpd.server_address}")
        return self.__httpd.serve_forever

    @override
    def stop(self):
        if self.__httpd is None:
            raise RuntimeError("HTTP server is not running")
        self.logger("Stopping HTTP server")
        self.__httpd.shutdown()
        self.__httpd.server_close()
        if self._thread.is_alive():
            super().stop()
        self.__httpd = None
        self.logger("HTTP server stopped")


class GitServer(BaseServer):
    def __init__(self, directory: Path, port: int, logger):
        super().__init__(directory, port, logger)
        self.__pid_file = directory / "git-server.pid"
        self.__pid: Optional[int] = None

    @override
    def _target(self) -> Callable[[], object]:
        def target() -> None:
            self.logger(f"Starting GIT server at {self.directory}")
            exit_code = subprocess_rt.run(
                [
                    "git",
                    "daemon",
                    "--verbose",
                    "--export-all",
                    "--reuseaddr",
                    "--detach",
                    "--listen=localhost",
                    f"--port={self.port}",
                    f"--pid-file={self.__pid_file}",
                    f"--base-path={self.directory}",
                ],
                printer=self.logger,
            )

            if exit_code != 0:
                raise RuntimeError(f"git daemon exited with code {exit_code}")

            try:
                if self.__pid_file.exists():
                    with open(self.__pid_file, "r", encoding="utf-8") as f:
                        pid_content = f.read().strip()
                        if pid_content:
                            self.__pid = int(pid_content)
                            self.logger(
                                f"GIT server started at localhost:{self.port} "
                                f"and with pid {self.__pid}"
                            )
                        else:
                            raise RuntimeError("PID file is empty")
                else:
                    raise RuntimeError(f"PID file {self.__pid_file} was not created")
            except (FileNotFoundError, ValueError, OSError) as e:
                raise RuntimeError(f"Failed to read PID file: {e}")

        return target

    @override
    def stop(self):
        if self._thread is None:
            raise RuntimeError("GIT server is not running")
        self.logger(f"Stopping GIT server with pid {self.__pid}")
        if self._thread.is_alive():
            if self.__pid is not None:
                os.kill(self.__pid, signal.SIGTERM)
                super().stop()
            else:
                super().stop()
                raise RuntimeError("GIT server PID is undefined")
        self.__pid = None
        self.__pid_file.unlink(missing_ok=True)
        self.logger("GIT server stopped")
