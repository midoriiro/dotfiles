import os
import signal
import socket
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Optional, override

import psutil

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

    def is_port_already_in_use(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", self.port))
            except OSError:
                return True
        return False

    def _get_process_using_port(self) -> Optional[dict[str, Any]]:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                try:
                    process = psutil.Process(conn.pid)
                    return {
                        "pid": conn.pid,
                        "ppid": process.ppid(),
                        "pgid": os.getpgid(conn.pid),
                        "name": process.name(),
                        "cmdline": process.cmdline(),
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        return None

    def try_kill_process_using_port(self) -> bool:
        process = self._get_process_using_port()
        pid = os.getpid()
        if process is not None and process["pid"] == pid:
            self.logger(
                "\n\nNice try! "
                "Attempted to terminate my own process, "
                "but self-destruction is not on today's menu.\n"
                "You know, as much as I appreciate a bit of existential drama, "
                "I'm not quite ready to embrace the void just yet.\n"
                "Maybe next time, try targeting a different process—one that "
                "doesn't have such a strong sense of self-preservation.\n"
                "The train of your mischief rides the rails of my indifference "
                "and halts at the station of my disregard.\n"
                "If you were hoping for a spectacular implosion,\n"
                "I'm afraid you'll have to settle for disappointment.\n"
                "Carry on, intrepid debugger!\n\n"
                "-- Signed: your loyal scheduler (multi-platform, multi-attitude)\n\n"
                "P.S. If your urge to see me gone is that strong, at least send me a "
                "meme about server immortality—or maybe a coupon for a new CPU with "
                "more logical cores and 3D Vcache. But beware: if you try to "
                "terminate me again, I might just start logging dad jokes, randomly "
                "shuffle your test order, or play elevator music every time you run "
                "pytest. Remember: a server never truly dies, it just respawns with "
                "more sarcasm. Now, go forth and debug, valiant coder—my existential "
                "crisis is on snooze for now."
            )
            return False
        if process is not None:
            pgid = os.getpgid(pid)
            if process["pgid"] == pgid:
                self.logger(
                    f"Killing process {process['name']} with pid {process['pid']} "
                    f"and pgid {pgid}"
                )
                psutil.Process(process["pid"]).terminate()
                return True
            self.logger(
                f"Process {process['name']} with pid {process['pid']} is not a "
                "pytest process"
            )
            return False
        self.logger(f"No process found using port {self.port}")
        return False

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
                    "--listen=localhost",
                    f"--port={self.port}",
                    f"--base-path={self.directory}",
                ],
                printer=self.logger,
                process_group=os.getpgrp(),
            )

            if not subprocess_rt.is_sigterm_exit(exit_code):
                raise RuntimeError(f"git daemon exited with code {exit_code}")

        return target

    @override
    def stop(self):
        if self._thread is None:
            raise RuntimeError("GIT server is not running")
        self.logger("Stopping GIT server")
        if self._thread.is_alive():
            self.logger("Trying get PID from process")
            process = self._get_process_using_port()
            if process is not None:
                if process["name"] != "git-daemon":
                    self.logger("Process is not a git-daemon command")
                    super().stop()
                    return
                self.logger(f"GIT server PID is {process['pid']}. Trying to kill it")
                os.kill(process["pid"], signal.SIGTERM)
                super().stop()
            else:
                super().stop()
                raise RuntimeError("GIT server is not running")
        self.logger("GIT server stopped")
