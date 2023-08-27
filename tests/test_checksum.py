"""Tests for the :mod:`gptsum.checksum` module."""

import hashlib
import math
import os
from pathlib import Path
from typing import BinaryIO

import pytest
import pytest_benchmark.fixture  # type: ignore[import]
from pytest_mock import MockerFixture

from gptsum import checksum, gpt
from tests import conftest


def test__posix_fadvise_sequential_not_supported(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """Test `_posix_fadvise_sequential` when `posix_fadvise` is not supported."""
    monkeypatch.delattr(os, "posix_fadvise", raising=False)

    with open(conftest.TESTDATA_DISK, "rb") as fd:
        checksum._posix_fadvise_sequential(
            fd.fileno(), 0, os.fstat(fd.fileno()).st_size
        )


@pytest.mark.skipif(
    not hasattr(os, "posix_fadvise"), reason="No support for posix_fadvise"
)
def test__posix_fadvise_sequential(
    mocker: MockerFixture,
) -> None:
    """Test `_posix_fadvise_sequential`."""
    mocked = mocker.patch("os.posix_fadvise")

    with open(conftest.TESTDATA_DISK, "rb") as fd:
        checksum._posix_fadvise_sequential(
            fd.fileno(), 0, os.fstat(fd.fileno()).st_size
        )

        # Make mypy happy
        assert hasattr(os, "POSIX_FADV_SEQUENTIAL")

        assert mocked.called_with(
            fd.fileno(), 0, os.fstat(fd.fileno()).st_size, os.POSIX_FADV_SEQUENTIAL
        )


def blake2b(fd: BinaryIO) -> bytes:
    """Calculate the Blake2b digest of a file.

    :param fd: File-like object of which to calculate the digest

    :returns: Blake2b digest of the file contents
    """
    hasher = hashlib.blake2b(digest_size=16)

    size = os.fstat(fd.fileno()).st_size
    checksum.hash_file(hasher.update, fd.fileno(), size, 0)

    return hasher.digest()


def test_hash_file(monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture) -> None:
    """Test `checksum.hash_file`."""
    mocked = mocker.patch("os.preadv", side_effect=os.preadv)

    expected_reads = 0

    with open(conftest.TESTDATA_DISK, "rb") as fd:
        # Full read
        hasher = hashlib.sha1()  # noqa: S303, S324
        size = os.fstat(fd.fileno()).st_size
        result = checksum.hash_file(hasher.update, fd.fileno(), size, offset=0)

        assert result == size
        # sha1sum tests/testdata/disk
        assert hasher.hexdigest() == "fdb8443238315360e1c15940e07d5249127fb909"

        expected_reads += math.floor(
            (result + checksum._BUFFSIZE - 1) / checksum._BUFFSIZE
        )

        # Test 'partial' read: we can read `buffsize` from the file, but are
        # only processing part of said data.
        hasher = hashlib.sha1()  # noqa: S303, S324
        size = 2 * checksum._BUFFSIZE + int(checksum._BUFFSIZE / 2 - 1)

        assert size % checksum._BUFFSIZE != 0
        assert os.fstat(fd.fileno()).st_size > size

        result = checksum.hash_file(hasher.update, fd.fileno(), size, offset=0)

        assert result == size
        # $ dd if=tests/testdata/disk bs=1 \
        #     count=$(( 2 * 128 * 1024 + 64 * 1024 - 1 )) | sha1sum
        assert hasher.hexdigest() == "a40ca827c1023a67b5d430b61abd37d05cb681a2"

        expected_reads += math.floor(
            (result + checksum._BUFFSIZE - 1) / checksum._BUFFSIZE
        )

    mocked.assert_called()
    assert mocked.call_count == expected_reads


def test_calculate() -> None:
    """Test checksum calculation of an image twice."""
    with gpt.GPTImage(path=conftest.TESTDATA_DISK, open_mode=os.O_RDONLY) as image:
        digest1 = checksum.calculate(image)
        digest2 = checksum.calculate(image)

        assert digest2 == digest1
        assert digest1 == conftest.TESTDATA_EMBEDDED_DISK_GUID.bytes

    with gpt.GPTImage(
        path=conftest.TESTDATA_EMBEDDED_DISK, open_mode=os.O_RDONLY
    ) as image:
        assert checksum.calculate(image) == conftest.TESTDATA_EMBEDDED_DISK_GUID.bytes


def test_calculate_inplace(disk_image: Path) -> None:
    """Test :func:`checksum.calculate` by modifying in image in-place."""
    with open(disk_image, "rb") as fd:
        real_hash = blake2b(fd)

    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        digest = checksum.calculate(image)
        assert digest != real_hash

    # Overwrite CRCs and GUIDs with zeros, in-place
    with open(disk_image, "rb+") as fd:
        header_crc32_offset = 8 + 4 + 4
        guid_offset = header_crc32_offset + 4 + 4 + 8 + 8 + 8 + 8

        gpt.pwrite_all(fd.fileno(), b"\0" * 4, gpt.MBR_SIZE + header_crc32_offset)
        gpt.pwrite_all(fd.fileno(), b"\0" * 16, gpt.MBR_SIZE + guid_offset)

        size = os.fstat(fd.fileno()).st_size
        gpt.pwrite_all(
            fd.fileno(), b"\0" * 4, size - gpt.LBA_SIZE + header_crc32_offset
        )
        gpt.pwrite_all(fd.fileno(), b"\0" * 16, size - gpt.LBA_SIZE + guid_offset)

    with open(disk_image, "rb") as fd:
        new_hash = blake2b(fd)

        assert new_hash == digest


def test_calculate_benchmark(
    monkeypatch: pytest.MonkeyPatch,
    benchmark: pytest_benchmark.fixture.BenchmarkFixture,
) -> None:
    """Benchmark :func:`checksum.calculate`."""
    with gpt.GPTImage(path=conftest.TESTDATA_DISK, open_mode=os.O_RDONLY) as image:
        benchmark(checksum.calculate, image)


def test_digest_to_guid() -> None:
    """Test :func:`checksum.digest_to_guid`."""
    hasher = hashlib.blake2b(digest_size=16)
    hasher.update(b"\0" * 32)
    digest = hasher.digest()
    guid = checksum.digest_to_guid(digest)
    assert guid.bytes == digest
