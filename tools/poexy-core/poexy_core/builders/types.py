from pathlib import Path
from typing import Callable, Union

FilePathPredicate = Callable[[Path], Union[Path, None]]
FilePathCallback = Callable[[Path, Path], None]
LinkPathCallback = Callable[[Path, Path, Path], None]
