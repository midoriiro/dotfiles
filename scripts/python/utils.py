import sys
import os
import subprocess

# Force UTF-8 encoding for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    # Reconfigure stdout and stderr to use UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def safe_print(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII if emoji encoding fails
        fallback_map = {
            "🔄": "[INFO]",
            "❌": "[ERROR]",
            "✅": "[SUCCESS]",
            "🚀": "[START]",
            "🎉": "[SUCCESS]"
        }
        for emoji, replacement in fallback_map.items():
            text = text.replace(emoji, replacement)
        print(text)

def safe_print_info(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🔄 {text}")

def safe_print_error(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"❌ {text}")

def safe_print_success(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"✅ {text}")

def safe_print_start(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🚀 {text}")

def safe_print_done(text: str) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🎉 {text}")

def safe_subprocess_run(cmd: list[str]) -> int:
    """Run subprocess with proper encoding for Windows compatibility."""
    # Force UTF-8 encoding for subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    # On Windows, set additional encoding environment variables
    if sys.platform == 'win32':
        env['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

    arguments_to_append = {
        'stdout': subprocess.PIPE, 
        'shell': False,
        'text': True,
        'encoding': 'utf-8'
    }

    process = subprocess.Popen(cmd, env=env, **arguments_to_append)


    while True:
        output = process.stdout.readline()
        if output:
            safe_stdout_text(output.strip())
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