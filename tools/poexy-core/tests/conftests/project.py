import contextlib
import os
from contextlib import _GeneratorContextManager
from pathlib import Path
from typing import Callable

import pytest

from poexy_core import api
from poexy_core.pyproject.toml import PyProjectTOML


@pytest.fixture(scope="session")
def self_project() -> Path:
    project_path = Path(api.__file__).resolve().parent.parent
    return project_path


@pytest.fixture()
def sample_project(samples_path) -> Callable[[str], Path]:
    def _sample_project(name: str):
        project_path = samples_path / name
        return project_path

    return _sample_project


@pytest.fixture(scope="session")
def project() -> Callable[[Path], _GeneratorContextManager[None, None, None]]:
    @contextlib.contextmanager
    def _project(project_path: Path):
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"Pyproject.toml not found in {project_path}")

        old_cwd = os.getcwd()
        try:
            os.chdir(project_path)
            yield
        finally:
            os.chdir(old_cwd)

    return _project


@pytest.fixture()
def pyproject():
    def _pyproject():
        cwd = Path.cwd()
        return PyProjectTOML(path=cwd)

    return _pyproject
