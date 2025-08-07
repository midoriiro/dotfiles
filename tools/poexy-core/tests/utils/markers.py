import json
import time
from pathlib import Path
from typing import Dict


class MarkerFile:
    def __init__(self, path: Path, extra: Dict[str, str] = None):
        self.path = path
        self.__data = extra or {}
        self.__counter = 0

    def read(self) -> Dict[str, str]:
        if not self.exists():
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            self.__data = json.load(f)
            self.__counter = self.__data.get("counter")
            del self.__data["counter"]
        return self.__data

    def __write(self, counter: int):
        with open(self.path, "w", encoding="utf-8") as f:
            self.__data["counter"] = counter
            json.dump(self.__data, f, indent=2)

    def exists(self) -> bool:
        return self.path.exists() and self.path.is_file()

    def touch(self):
        if not self.exists():
            self.path.touch()
            self.__counter = 0
        else:
            self.read()

        self.__counter += 1

        self.__write(self.__counter)

    def untouch(self, wait: bool = False, timeout: float = 10) -> bool:
        if not self.exists():
            return False

        self.read()

        self.__counter -= 1

        if self.__counter == 0:
            self.path.unlink()
            return True

        self.__write(self.__counter)

        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout:
                self.read()
                if self.__counter == 0:
                    self.path.unlink()
                    return True
                time.sleep(0.1)
            if self.exists():
                self.path.unlink()
            return True

        return False
