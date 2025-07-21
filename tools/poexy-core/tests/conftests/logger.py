import logging

import pytest

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def root_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(logging.StreamHandler())
    return logger


@pytest.fixture(autouse=True)
def set_logger_level(caplog):
    caplog.at_level(logging.INFO)


@pytest.fixture(scope="session")
def log_info(root_logger):
    def _log_info(message):
        root_logger.info(message)

    return _log_info


@pytest.fixture(scope="session")
def log_info_section(log_info):
    def _log_info_section(message):
        pad = "=" * 20
        log_info(f"\n{pad} {message} {pad}\n")

    return _log_info_section
