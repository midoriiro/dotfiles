from typing import Optional

from poexy_core.manifest.types import ManifestStorage

MULTILINE_PREFIX = " " * 7 + "|"


def __get_storage_item(storage: ManifestStorage, key: str) -> Optional[int]:
    for index, item in enumerate(storage):
        if item[0] == key:
            return index
    return None


def _parse_multiline_value(
    storage: ManifestStorage, item_key: Optional[str], line: str
):
    if item_key is None:
        raise ValueError("Not key found for multiline value")
    storage_item_index = __get_storage_item(storage, item_key)
    if storage_item_index is None:
        raise ValueError(f"Key {item_key} not found in storage")
    storage_item_key, storage_item_value = storage[storage_item_index]
    if isinstance(storage_item_value, str):
        if MULTILINE_PREFIX in line:
            line = line.replace(MULTILINE_PREFIX, "").strip()
        storage[storage_item_index] = (
            storage_item_key,
            storage_item_value + "\n" + line,
        )
    else:
        raise ValueError(f"Key {item_key} multiline value is not a string")


def __parse_single_line_value(storage: ManifestStorage, line: str) -> str:
    key, value = line.split(":", 1)
    storage_item_index = __get_storage_item(storage, key)
    if storage_item_index is None:
        storage.append((key, value.strip()))
    else:
        storage_item_key, storage_item_value = storage[storage_item_index]
        if isinstance(storage_item_value, str):
            storage_item_value = [storage_item_value]
        if isinstance(storage_item_value, list):
            storage[storage_item_index] = (
                storage_item_key,
                [*storage_item_value, value],
            )
        elif isinstance(storage_item_value, tuple):
            storage[storage_item_index] = (
                storage_item_key,
                (*storage_item_value, value),
            )
        else:
            raise ValueError(f"Unknown value type: {type(storage_item_value)}")
    return key


def parse(text: str) -> ManifestStorage:
    storage: ManifestStorage = []
    last_key: Optional[str] = None
    for line in text.splitlines():
        if line.strip() == "":
            continue
        if line.startswith(MULTILINE_PREFIX):
            _parse_multiline_value(storage, last_key, line)
        else:
            last_key = __parse_single_line_value(storage, line)
    return storage


def to_string(storage: ManifestStorage) -> str:
    text = ""
    for key, value in storage:
        if isinstance(value, str):
            text += f"{key}: {value}\n"
        elif isinstance(value, list):
            for item in value:
                text += f"{key}: {item}\n"
        elif isinstance(value, tuple):
            for item in value:
                text += f"{key}: {item}\n"
        else:
            raise ValueError(f"Unknown value type: {type(value)}")
    return text
