import subprocess
from pathlib import Path
from typing import Callable, List

import pytest

# pylint: disable=subprocess-run-check


@pytest.fixture()
def execute_binary() -> Callable[[Path, List[str]], subprocess.CompletedProcess]:
    def execute(binary_path: Path, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run([binary_path, *args], capture_output=True, text=True)

    return execute
