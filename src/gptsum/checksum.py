"""GPT disk image checksum calculation."""

import hashlib
import os
import uuid
from typing import Callable, List, Union, cast

from gptsum import gpt

ZERO_GUID = uuid.UUID(bytes=b"\0" * 16)


def hash_file(
    fn: Callable[[Union[bytes, memoryview]], None], fd: int, size: int, offset: int
) -> int:
    """Repeatedly call a function on a slice of a file."""
    buffsize = 128 * 1024
    done = 0

    os.posix_fadvise(
        fd, offset, size, os.POSIX_FADV_SEQUENTIAL | os.POSIX_FADV_WILLNEED
    )

    if hasattr(os, "preadv"):
        preadv = cast(
            Callable[[int, List[bytearray], int], int],
            getattr(os, "preadv"),  # noqa: B009
        )

        buff = bytearray(buffsize)
        bufflist = [buff]
        view = memoryview(buff)

        while size > 0:
            n = preadv(fd, bufflist, offset)

            n = min(n, size)

            if n < buffsize:
                fn(view[:n])
            else:
                fn(view)

            done += n
            size -= n
            offset += n
    else:  # Python <= 3.6
        while size > 0:
            data = os.pread(fd, buffsize, offset)
            datasize = len(data)

            n = min(datasize, size)

            if n < datasize:
                fn(data[:n])
            else:
                fn(data)

            done += n
            size -= n
            offset += n

    return done


def calculate(image: gpt.GPTImage) -> bytes:
    """Calculate the 16-byte checksum of the given image."""
    fd = image.fileno()

    hasher = hashlib.blake2b(digest_size=16)
    offset = 0

    mbr = gpt.pread_all(fd, gpt.MBR_SIZE, 0)
    hasher.update(mbr)
    offset += len(mbr)

    primary = image.read_primary_gpt_header()
    primary_with_zero_guid = primary.with_new_guid(ZERO_GUID)
    hasher.update(primary_with_zero_guid.pack(override_crc32=0))
    offset += len(primary.pack())

    last = os.fstat(fd).st_size - gpt.GPT_HEADER_SIZE

    offset += hash_file(hasher.update, fd, last - offset, offset)

    assert offset == os.fstat(fd).st_size - gpt.GPT_HEADER_SIZE  # noqa: S101

    backup = image.read_backup_gpt_header()
    backup_with_zero_guid = backup.with_new_guid(ZERO_GUID)
    hasher.update(backup_with_zero_guid.pack(override_crc32=0))
    offset += len(backup.pack())

    assert offset == os.fstat(fd).st_size  # noqa: S101

    return hasher.digest()


def digest_to_guid(digest: bytes) -> uuid.UUID:
    """Convert a 16-byte digest into a GUID."""
    return uuid.UUID(bytes=digest)
