"""Various utility functions."""

import hashlib
import itertools
import os
from pathlib import Path

from gptsum import checksum


def _sha256sum(fd: int) -> str:
    """Calculate the SHA256 digest of a file given a file descriptor."""
    digest = hashlib.sha256()

    size = os.fstat(fd).st_size
    done = checksum.hash_file(digest.update, fd, size, 0)

    assert done == size

    return digest.hexdigest()


def assert_files_equal(file1: Path, file2: Path, *others: Path) -> None:
    """Check whether (the checksum of) files are equal."""
    digests = []

    for file in itertools.chain([file1, file2], others):
        with open(file, "rb") as fd:
            digest = _sha256sum(fd.fileno())
            digests.append(digest)

    assert digests == [digests[0]] * len(digests)
