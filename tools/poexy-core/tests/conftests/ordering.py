import time
from pathlib import Path
from typing import List, Self

import pytest
from filelock import FileLock

from tests.utils.markers import MarkerFile

# pylint: disable=redefined-outer-name


class SerialTest(dict):
    def __init__(self, nodeid: str, completed: bool = False):
        super().__init__(nodeid=nodeid, completed=completed)

    @staticmethod
    def from_dict(**kwargs) -> Self:
        return SerialTest(**kwargs)

    @staticmethod
    def read_marker_file(marker_file: MarkerFile) -> List[Self]:
        marker_data = marker_file.read()
        return list(map(lambda x: SerialTest.from_dict(**x), marker_data["collected"]))

    @property
    def nodeid(self):
        return self["nodeid"]

    @property
    def completed(self):
        return self["completed"]

    @completed.setter
    def completed(self, value):
        self["completed"] = value


def pytest_collection_modifyitems(
    config,  # pylint: disable=unused-argument
    items,
):
    serial = []
    others = []

    for item in items:
        if "serial" in item.keywords:
            serial.append(item)
        else:
            others.append(item)

    items[:] = serial + others


@pytest.fixture(scope="session", autouse=True)
def serial_test_registry(request: pytest.FixtureRequest, serial_lock_path: Path):
    serial_tests: List[SerialTest] = []
    lock_path = serial_lock_path / ".lock"
    lock = FileLock(lock_path)

    with lock:
        marker_file = MarkerFile(serial_lock_path / ".collected")

        if not marker_file.exists():
            session: pytest.Session = request.node
            for item in session.items:
                for marker in item.own_markers:
                    if marker.name == "serial":
                        serial_tests.append(SerialTest(item.nodeid))
            marker_file.extra = {"collected": serial_tests}
        else:
            serial_tests: List[SerialTest] = SerialTest.read_marker_file(marker_file)
        marker_file.touch()

    return serial_tests


@pytest.fixture(scope="function", autouse=True)
def serial_test_coordinator(
    request: pytest.FixtureRequest,
    serial_test_registry: List[SerialTest],
    serial_lock_path: Path,
    worker_id,
):
    if worker_id == "master":
        # If we are on the master process, we don't need to coordinate serial tests
        # because the master process will run all serial tests in order.
        yield
        return

    lock_path = serial_lock_path / ".lock"
    lock = FileLock(lock_path)

    marker_file = MarkerFile(serial_lock_path / ".collected")

    node: pytest.Function = request.node

    if any([x.nodeid == node.nodeid for x in serial_test_registry]):
        is_serial = True
    else:
        is_serial = False

    if is_serial:
        with lock:
            yield
            serial_tests: List[SerialTest] = SerialTest.read_marker_file(marker_file)
            for test in serial_tests:
                if test.nodeid == node.nodeid:
                    test.completed = True
                    break
            marker_file.extra = {"collected": serial_tests}
            marker_file.write()
            return

    all_serial_tests_completed = False

    while not all_serial_tests_completed:
        with lock:
            serial_tests: List[SerialTest] = SerialTest.read_marker_file(marker_file)
            all_serial_tests_completed = all([x.completed for x in serial_tests])
            if all_serial_tests_completed:
                break

        time.sleep(0.25)

    yield
