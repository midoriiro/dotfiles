import os
import subprocess
import sys
from typing import Callable

Printer = Callable[[str], None]

def run(cmd: list[str], printer: Printer, **kwargs) -> int:
    """Run subprocess with proper encoding for Windows compatibility."""
    # Force UTF-8 encoding for subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    # On Windows, set additional encoding environment variables
    if sys.platform == 'win32':
        env['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

    arguments = {
        'stdout': subprocess.PIPE, 
        'stderr': subprocess.STDOUT,
        'shell': False,
        'text': True,
        'encoding': 'utf-8'
    }

    arguments.update(kwargs)

    process = subprocess.Popen(cmd, env=env, **arguments)

    while True:
        output = process.stdout.readline()
        if output:
            printer(output.strip())
        if process.poll() is not None:
            break

    exit_code = process.poll()
    return exit_code


def safe_stdout_text(text: str) -> str:
    """Safely handle stdout text that might be None or have encoding issues."""
    if text is None:
        return ""
    
    try:
        # Try to decode as UTF-8 first
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='replace')
        return str(text)
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback to ASCII with replacement
        if isinstance(text, bytes):
            return text.decode('ascii', errors='replace')
        return str(text).encode('ascii', errors='replace').decode('ascii') 