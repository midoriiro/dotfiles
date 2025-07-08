import os
import subprocess
import sys
from typing import Callable, List

Printer = Callable[[str], None]

def run(cmd: List[str], printer: Printer, **kwargs) -> int:
    arguments = {
        'stdout': subprocess.PIPE, 
        'stderr': subprocess.STDOUT,
        'shell': False,
        'text': True,
        'encoding': 'utf-8'
    }

    arguments.update(kwargs)

    process = subprocess.Popen(cmd, **arguments)

    while True:
        output = process.stdout.readline()
        if output:
            printer(output.strip())
        if process.poll() is not None:
            break

    exit_code = process.poll()
    return exit_code