import os
import sys
from typing import Callable


Printer = Callable[[str], None]

# Force UTF-8 encoding for Windows compatibility
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    # Reconfigure stdout and stderr to use UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def safe_print(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    try:
        printer(text)
    except UnicodeEncodeError:
        # Fallback to ASCII if emoji encoding fails
        fallback_map = {
            "🔄": "[INFO]",
            "❌": "[ERROR]",
            "✅": "[SUCCESS]",
            "⚠️": "[WARNING]",
            "🚀": "[START]",
            "🎉": "[SUCCESS]"
        }
        for emoji, replacement in fallback_map.items():
            text = text.replace(emoji, replacement)
        printer(text)

def safe_print_info(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🔄 {text}", printer=printer)

def safe_print_error(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"❌ {text}", printer=printer)

def safe_print_success(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"✅ {text}", printer=printer)

def safe_print_warning(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"⚠️ {text}", printer=printer)

def safe_print_start(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🚀 {text}", printer=printer)

def safe_print_done(text: str, printer: Printer) -> None:
    """Print text with emoji fallback for Windows compatibility."""
    safe_print(f"🎉 {text}", printer=printer)