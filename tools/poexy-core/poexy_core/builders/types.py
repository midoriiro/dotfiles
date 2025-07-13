from pathlib import Path
from typing import Callable, Union

FilePathPredicate = Callable[[Path], Union[Path, None]]
FilePathCallback = Callable[[Path, Path], Union[Path, None]]
