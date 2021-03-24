"""Fake test module so :mod:`gptsum.__main__` gets imported."""

import runpy
import sys

from pytest_mock import MockerFixture


def test_main(mocker: MockerFixture) -> None:
    """Test running the :mod:`gptsum` package."""
    mocker.patch("sys.argv", sys.argv[:1])
    # Once for real
    runpy.run_module("gptsum", run_name="__main__", alter_sys=True)
    # Once to please the coverage checks
    runpy.run_module("gptsum", alter_sys=True)
