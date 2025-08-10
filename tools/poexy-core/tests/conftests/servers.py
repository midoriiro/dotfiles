import shutil
from pathlib import Path

import pytest
from filelock import FileLock

from poexy_core.utils import subprocess_rt
from tests.utils.markers import MarkerFile
from tests.utils.servers import GitServer, HttpServer

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def server_usage(request):
    session = request.node
    use_http_server = False
    use_git_server = False
    for item in session.items:
        for marker in item.own_markers:
            if marker.name == "use_http_server":
                use_http_server = True
            elif marker.name == "use_git_server":
                use_git_server = True
    usage = {
        "http_server": use_http_server,
        "git_server": use_git_server,
    }
    return usage


@pytest.fixture(scope="session", autouse=True)
def serve_library_archive(
    server_usage,
    http_server_path: Path,
    samples_path: Path,
    server_lock_path: Path,
    log_info_section,
    log_info,
) -> None:
    if not server_usage["http_server"]:
        yield
        return

    lock_path = server_lock_path / ".http.lock"
    lock = FileLock(lock_path)

    http_server = None

    with lock:
        marker_file = MarkerFile(http_server_path / ".server_running")

        if not marker_file.exists():
            log_info_section("Removing http server folder")
            shutil.rmtree(http_server_path, ignore_errors=True)

            log_info_section("Creating http server folder")
            http_server_path.mkdir(parents=True, exist_ok=True)

            log_info_section("Serving library archive")
            library_path = (
                samples_path
                / "core_functionality"
                / "library"
                / "library-1.0.0-py3-none-any.whl"
            )
            shutil.copy(library_path, http_server_path)
            http_server = HttpServer(http_server_path, 8000, log_info)
            if http_server.is_port_already_in_use():
                if not http_server.try_kill_process_using_port():
                    raise RuntimeError("Port 8000 is already in use")
            http_server.start()
            http_server.wait_for_connection(timeout=30)

        marker_file.touch()

    try:
        yield
    finally:
        if (
            marker_file.untouch(wait=http_server is not None)
            and http_server is not None
        ):
            http_server.stop()
            log_info_section("Removing http server folder")
            shutil.rmtree(http_server_path, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def serve_library_vcs(
    server_usage,
    git_server_path: Path,
    samples_path: Path,
    server_lock_path: Path,
    log_info_section,
    log_info,
) -> None:
    if not server_usage["git_server"]:
        yield
        return

    lock_path = server_lock_path / ".vcs.lock"
    lock = FileLock(lock_path)

    git_server = None

    with lock:
        marker_file = MarkerFile(git_server_path / ".server_running")

        if not marker_file.exists():
            log_info_section("Removing git server folder")
            shutil.rmtree(git_server_path, ignore_errors=True)

            log_info_section("Creating git server folder")
            git_server_path.mkdir(parents=True, exist_ok=True)

            log_info_section("Serving library vcs")

            working_path = git_server_path / "work"
            working_path.mkdir(parents=True, exist_ok=True)

            bare_path = git_server_path / "library.git"
            bare_path.mkdir(parents=True, exist_ok=True)

            library_path = samples_path / "core_functionality" / "library"
            shutil.copytree(library_path, working_path, dirs_exist_ok=True)

            subprocess_rt.run(["git", "init"], printer=log_info, cwd=working_path)
            subprocess_rt.run(
                ["git", "branch", "-m", "main"], printer=log_info, cwd=working_path
            )
            subprocess_rt.run(
                ["git", "config", "user.email", "ci@example.com"],
                printer=log_info,
                cwd=working_path,
            )
            subprocess_rt.run(
                ["git", "config", "user.name", "CI"], printer=log_info, cwd=working_path
            )
            subprocess_rt.run(["git", "add", "-A"], printer=log_info, cwd=working_path)
            subprocess_rt.run(
                ["git", "commit", "-m", "Initial commit"],
                printer=log_info,
                cwd=working_path,
            )

            subprocess_rt.run(
                ["git", "init", "--bare", str(bare_path)], printer=log_info
            )
            subprocess_rt.run(
                ["git", "remote", "add", "origin", str(bare_path)],
                printer=log_info,
                cwd=working_path,
            )
            subprocess_rt.run(
                ["git", "push", "origin", "main"], printer=log_info, cwd=working_path
            )
            subprocess_rt.run(
                ["git", "symbolic-ref", "HEAD", "refs/heads/main"],
                printer=log_info,
                cwd=bare_path,
            )
            (bare_path / "git-daemon-export-ok").touch()

            git_server = GitServer(bare_path.parent, 8001, log_info)
            if git_server.is_port_already_in_use():
                if not git_server.try_kill_process_using_port():
                    raise RuntimeError("Port 8001 is already in use")
            git_server.start()
            git_server.wait_for_connection(timeout=30)

        marker_file.touch()

    try:
        yield
    finally:
        if marker_file.untouch(wait=git_server is not None) and git_server is not None:
            git_server.stop()
            log_info_section("Removing git server folder")
            shutil.rmtree(git_server_path, ignore_errors=True)
