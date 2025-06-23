import logging
from pathlib import Path

import pytest
import typer

from merge.main import Format, TyperHandler, app


def test_typer_handler_emits_formatted_message(mocker):
    echo_mock = mocker.patch("typer.echo")

    handler = TyperHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    logger = logging.getLogger("unit-test.typer-handler")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.info("Hello coverage!")

    echo_mock.assert_called_once_with("INFO - Hello coverage!", err=True)

def test_typer_handler_emit_handles_exception(mocker):
    """
    When typer.echo raises, TyperHandler.emit must:
    1. Catch the exception (so logger.info() ne lève rien)
    2. Appeler handleError(record) exactement une fois
    """
    mocker.patch("typer.echo", side_effect=RuntimeError("simulated failure"))

    handler = TyperHandler()
    error_spy = mocker.spy(handler, "handleError")

    logger = logging.getLogger("unit-test.typer-handler-exception")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        logger.info("trigger failure")
    except Exception as exc:            # pragma: no cover
        pytest.fail(f"TyperHandler did not swallow exception: {exc}")

    error_spy.assert_called_once()


def test_main_module_execution():
    """Test that the main module can be executed directly."""
    import subprocess
    import sys
    from pathlib import Path

    # Get the path to main.py
    main_path = Path(__file__).parent.parent / "merge" / "main.py"
    
    # Run the module directly
    result = subprocess.run([sys.executable, str(main_path), "--help"], 
                          capture_output=True, 
                          text=True)
    
    assert result.returncode == 0
    assert "Usage:" in result.stdout 