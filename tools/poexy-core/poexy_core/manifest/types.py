from typing import Callable, List, Tuple, Union

from poexy_core.metadata.fields import MetadataField

ManifestKey = Union[str, MetadataField]
ManifestValue = Union[str, List[str], Tuple[str, ...]]
ManifestStorage = List[Tuple[str, ManifestValue]]
ManifestStorageOperation = Callable[[ManifestStorage], None]
