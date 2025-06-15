from pathlib import Path
from typing import Dict, Optional

import typer

from .models import Feature


class Context:
    def __init__(self):
        self.output: Optional[Path] = None
        self.dry_run: bool = False
        self.features: Dict[str, Feature] = {}

    def __str__(self) -> str:
        """Return a string representation of the context."""
        return (
            f"Context("
            f"output={self.output}, "
            f"dry_run={self.dry_run}, "
            f"features={list(self.features.keys())}"
            f")"
        )

    def __repr__(self) -> str:
        """Return a detailed string representation of the context."""
        return (
            f"Context("
            f"output={repr(self.output)}, "
            f"dry_run={repr(self.dry_run)}, "
            f"features={repr(self.features)}"
            f")"
        )
