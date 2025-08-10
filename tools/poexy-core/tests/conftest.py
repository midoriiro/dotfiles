# pylint: disable=wildcard-import,unused-wildcard-import
# flake8: noqa: F403,F401

from conftests.assert_builds import *
from conftests.assert_manifests import *
from conftests.executable import *
from conftests.logger import *
from conftests.metadata import *
from conftests.paths import *
from conftests.pip import *
from conftests.project import *
from conftests.servers import *


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "prevent_venv_self_build: mark test to prevent venv self build"
    )
    config.addinivalue_line(
        "markers", "use_http_server: mark test to run setup http server fixture"
    )
    config.addinivalue_line(
        "markers", "use_git_server: mark test to run setup git server fixture"
    )
    config.addinivalue_line(
        "markers", "file_operation: mark test to run setup file operation fixture"
    )
