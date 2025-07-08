import mmap
from pathlib import Path
import tomllib
from typing import Dict, List, Union

ENTRY_POINT_SEARCH_STRING_1 = b'if __name__ == "__main__":'
ENTRY_POINT_SEARCH_STRING_2 = b"if __name__ == '__main__':"

class PyprojectError(Exception):
    pass

class Pyproject:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.__ensure_poetry_project()
        pyproject_path = self.project_path / "pyproject.toml"
        with open(pyproject_path, "rb") as file:
            self.pyproject = tomllib.load(file)

    def __ensure_poetry_project(self):
        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise PyprojectError(f"Not a Poetry project: {self.project_path}")

    @property
    def project_name(self) -> str:
        if "project" in self.pyproject:
            return self.pyproject["project"]["name"]
        else:
            return self.pyproject["tool"]["poetry"]["name"]

    @property
    def project_version(self) -> str:
        if "project" in self.pyproject:
            return self.pyproject["project"]["version"]
        else:
            return self.pyproject["tool"]["poetry"]["version"]
    
    def __search_poetry_packages(self, packages: List[Dict]) -> Path:
        def search_package(package: dict) -> Path:
            if "include" in package and "from" not in package:
                return Path(package["include"])
            elif "from" in package:
                return Path(package["from"])
            else:
                raise PyprojectError("Invalid packages format in pyproject.toml")
        
        includes = [search_package(package) for package in packages]

        if len(includes) > 1:
            raise PyprojectError("Multiple packages found in pyproject.toml. Please specify the package to use either in tool.poetry.packages or in tool.poexy.package section.")
        return includes[0]
    
    @property
    def package_path(self) -> Path:
        poetry = self.pyproject["tool"]["poetry"]
        poetry_packages = poetry["packages"]
        if  poetry_packages:
            if isinstance(poetry_packages, list):
                return self.__search_poetry_packages(poetry_packages)
            else:
                raise PyprojectError("Invalid packages format in pyproject.toml")
        else:
            poexy = self.pyproject["tool"]["poexy"]
            if "package" in poexy:
                return Path(poexy["package"])
            else:
                raise PyprojectError("No package found in pyproject.toml. Please specify the package to use in tool.poexy.package section.")
            
    def __search_entry_point_file(self, path: Path) -> Union[Path, None]:
        with open(path, 'rb', buffering=0) as file:
            data = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
            matched_first_pattern = data.find(ENTRY_POINT_SEARCH_STRING_1) != -1
            matched_second_pattern = data.find(ENTRY_POINT_SEARCH_STRING_2) != -1
            if matched_first_pattern or matched_second_pattern:
                return path
            else:
                return None
            
    def __search_entry_point(self, path: Path) -> Union[List[Path], None]:
        result = []
        for path in path.iterdir():
            if path.is_dir():
                entry_point = self.__search_entry_point(path)
                if entry_point:
                    result.extend(entry_point)
            elif path.is_file() and path.suffix == ".py":
                entry_point = self.__search_entry_point_file(path)
                if entry_point:
                    result.append(entry_point)
        if len(result) == 0:
            return None
        return result
    
    @property
    def entry_point(self) -> str:
        poexy = self.pyproject["tool"]["poexy"]
        if "entry-point" in poexy:
            return poexy["entry-point"]
        else:            
            entry_points = self.__search_entry_point(self.project_path)

            if len(entry_points) == 0:
                raise PyprojectError("No entry point found in pyproject.toml. Please specify the entry point to use in tool.poexy.entry-point section.")
            elif len(entry_points) == 1:
                return entry_points[0]
            else:
                raise PyprojectError("Multiple entry points found in pyproject.toml. Please specify the entry point to use in tool.poexy.entry-point section.")
            
    @property
    def executable_name(self) -> str:
        poexy = self.pyproject["tool"]["poexy"]
        if "executable-name" in poexy:
            return poexy["executable-name"]
        else:
            return self.project_name