import subprocess
from pathlib import Path
from typing import Callable, List, Optional

import pytest

# pylint: disable=subprocess-run-check


@pytest.fixture()
def execute_binary() -> Callable[[Path, List[str]], subprocess.CompletedProcess]:
    def execute(
        binary_path: Path, args: Optional[List[str]] = None
    ) -> subprocess.CompletedProcess:
        if args is None:
            cmd = [str(binary_path)]
        else:
            cmd = [str(binary_path), *args]
        return subprocess.run(cmd, capture_output=True, text=True)

    return execute
