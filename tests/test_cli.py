"""Tests for the :mod:`gptsum.cli` module."""

import hashlib
import os
import uuid
from pathlib import Path

import pytest

import gptsum
from gptsum import checksum, cli
from tests import conftest


def test_no_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the CLI without any options."""
    cli.main([])

    captured = capsys.readouterr()
    assert captured.out.startswith("usage: ")


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the CLI :option:`--verbose` option."""
    with pytest.raises(SystemExit):
        cli.main(["--version"])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(gptsum.__version__)


@pytest.mark.parametrize(
    ("disk_file", "expected_guid"),
    [
        (conftest.TESTDATA_DISK, conftest.TESTDATA_DISK_GUID),
        (conftest.TESTDATA_EMBEDDED_DISK, conftest.TESTDATA_EMBEDDED_DISK_GUID),
    ],
)
def test_get_guid(
    capsys: pytest.CaptureFixture[str],
    disk_file: Path,
    expected_guid: uuid.UUID,
) -> None:
    """Test the CLI :option:`get-guid` subcommand."""
    cli.main(["get-guid", str(disk_file)])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(expected_guid)


@pytest.mark.parametrize(
    ("disk_file", "expected_guid"),
    [
        (conftest.TESTDATA_DISK, conftest.TESTDATA_EMBEDDED_DISK_GUID),
        (conftest.TESTDATA_EMBEDDED_DISK, conftest.TESTDATA_EMBEDDED_DISK_GUID),
    ],
)
def test_calculate_expected_guid(
    capsys: pytest.CaptureFixture[str], disk_file: Path, expected_guid: uuid.UUID
) -> None:
    """Test the CLI :option:`calculate-expected-guid` subcommand."""
    cli.main(["calculate-expected-guid", str(disk_file)])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(expected_guid)


def test_set_guid(capsys: pytest.CaptureFixture[str], disk_image: Path) -> None:
    """Test the CLI :option:`set-guid` subcommand."""
    new_guid = uuid.UUID("bf85e1a8-748e-46f8-909f-4a70067efbe2")

    cli.main(["set-guid", str(disk_image), str(new_guid)])

    cli.main(["get-guid", str(disk_image)])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(new_guid)


def test_embed(capsys: pytest.CaptureFixture[str], disk_image: Path) -> None:
    """Test the CLI :option:`embed` subcommand."""
    cli.main(["embed", str(disk_image)])

    cli.main(["get-guid", str(disk_image)])

    captured = capsys.readouterr()
    assert captured.out == "{}\n".format(conftest.TESTDATA_EMBEDDED_DISK_GUID)

    hash1 = hashlib.sha256()
    with open(conftest.TESTDATA_EMBEDDED_DISK, "rb") as fd:
        size = os.fstat(fd.fileno()).st_size
        done = checksum.hash_file(hash1.update, fd.fileno(), size, 0)
        assert done == size

    hash2 = hashlib.sha256()
    with open(disk_image, "rb") as fd:
        size = os.fstat(fd.fileno()).st_size
        done = checksum.hash_file(hash2.update, fd.fileno(), size, 0)
        assert done == size

    assert hash1.hexdigest() == hash2.hexdigest()


def test_embed_noop(disk_image: Path) -> None:
    """Test to ensure issuing :option:`embed` on an already-prepared file is a no-op."""
    cli.main(["embed", str(disk_image)])
    stat1 = os.stat(disk_image)
    cli.main(["embed", str(disk_image)])
    stat2 = os.stat(disk_image)

    assert stat2.st_mtime == stat1.st_mtime
    assert stat2.st_ctime == stat1.st_ctime


def test_verify(disk_image: Path) -> None:
    """Test the CLI :option:`verify` subcommand."""
    cli.main(["verify", str(conftest.TESTDATA_EMBEDDED_DISK)])

    with pytest.raises(SystemExit):
        cli.main(["verify", str(disk_image)])

    cli.main(["embed", str(disk_image)])
    cli.main(["verify", str(disk_image)])
