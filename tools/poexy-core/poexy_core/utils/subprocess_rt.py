import subprocess
from typing import Callable, List

Printer = Callable[[str], None]


def run(cmd: List[str], printer: Printer, **kwargs) -> int:
    arguments = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "shell": False,
        "text": True,
        "encoding": "utf-8",
    }

    arguments.update(kwargs)

    process = subprocess.Popen(cmd, **arguments)

    while True:
        if process.stdout is None:
            continue
        output = process.stdout.readline()
        if output and output != "":
            printer(output.strip())
            continue
        if process.poll() is not None:
            break

    exit_code = process.poll()

    if exit_code is None:
        raise RuntimeError("Process terminated unexpectedly")

    return exit_code
