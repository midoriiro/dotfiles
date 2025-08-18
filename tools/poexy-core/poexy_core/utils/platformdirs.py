import sys
from pathlib import Path

from poexy_core.packages.files.models import PlatformDirectory


def _from_app_name(app_name: str):
    if sys.platform == "win32":
        data = f"{app_name}/share"
        config = f"{app_name}/config"
        cache = f"{app_name}/cache"
    elif sys.platform == "darwin":
        data = f"Application Support/{app_name}"
        config = f"Preferences/{app_name}"
        cache = f"Caches/{app_name}"
    elif sys.platform == "linux":
        data = f"share/{app_name}"
        config = f"etc/{app_name}"
        cache = f"var/cache/{app_name}"
    else:
        raise ValueError(f"Unsupported platform: {sys.platform}")
    return Path(data), Path(config), Path(cache)


class GenericPlatformDirectories:
    def __init__(self, app_name: str):
        self.__data = Path(f"{app_name}/{PlatformDirectory.Data.value}")
        self.__config = Path(f"{app_name}/{PlatformDirectory.Config.value}")
        self.__cache = Path(f"{app_name}/{PlatformDirectory.Cache.value}")

    @property
    def data(self):
        return self.__data

    @property
    def config(self):
        return self.__config

    @property
    def cache(self):
        return self.__cache


class PlatformDirectories(GenericPlatformDirectories):
    def __init__(self, app_name: str):
        self.__data, self.__config, self.__cache = _from_app_name(app_name)
