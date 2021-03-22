"""Tests for the :mod:`gptsum.cli` module."""

import gptsum
import gptsum.cli

import pytest


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the CLI :option:`--verbose` option."""
    with pytest.raises(SystemExit):
        gptsum.cli.main(["--version"])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(gptsum.__version__)
