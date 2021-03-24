"""Tests for the :mod:`gptsum.checksum` module."""

import hashlib
import os
from pathlib import Path
from typing import BinaryIO

import pytest_benchmark.fixture  # type: ignore[import]

from gptsum import checksum, gpt
from tests import conftest


def blake2b(fd: BinaryIO) -> bytes:
    """Calculate the Blake2b digest of a file.

    :param fd: File-like object of which to calculate the digest

    :returns: Blake2b digest of the file contents
    """
    hasher = hashlib.blake2b(digest_size=16)

    size = os.fstat(fd.fileno()).st_size
    checksum.hash_file(hasher.update, fd.fileno(), size, 0)

    return hasher.digest()


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
