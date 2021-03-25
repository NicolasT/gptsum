"""
gptsum: a tool to make disk images using GPT partitions self-verifiable.

Like `isomd5sum <https://github.com/rhinstaller/isomd5sum>`_.

This module exposes the functionality provided by the tool through a Python API.
"""

import dataclasses
import os
import sys
import uuid
from pathlib import Path
from typing import Callable, Optional, cast

if sys.version_info >= (3, 8):
    from importlib.metadata import Distribution, distribution
else:
    from importlib_metadata import Distribution, distribution

import gptsum
import gptsum.checksum
import gptsum.gpt

__metadata__ = cast(Callable[[str], Distribution], distribution)(__name__).metadata
__author__ = __metadata__["Author"]
"""Package author name.

.. versionadded:: 0.0.9
"""
__contact__ = __metadata__["Author-email"]
"""Package author contact e-mail address.

.. versionadded:: 0.0.9
"""
__license__ = __metadata__["License"]
"""Package license identifier.

.. versionadded:: 0.0.9
"""
__version__ = __metadata__["Version"]
"""Package version identifier.

.. versionadded:: 0.0.1
"""
del __metadata__


def _check_fd_or_path(fd: Optional[int], path: Optional[Path]) -> None:
    """Ensure either ``fd`` or ``path`` is given.

    >>> _check_fd_or_path(None, None)
    Traceback (most recent call last):
    ...
    ValueError: Either fd or path must be given

    >>> _check_fd_or_path(0, Path("/"))
    Traceback (most recent call last):
    ...
    ValueError: Both fd and path can't be given

    :param fd: Possible non-``None`` FD value
    :param path: Possiblel non-``None`` path value

    :raises ValueError: Both ``fd`` and ``path`` are ``None``
    :raises ValueError: Both ``fd`` and ``path`` are not ``None``
    """
    if fd is None and path is None:
        raise ValueError("Either fd or path must be given")
    if fd is not None and path is not None:
        raise ValueError("Both fd and path can't be given")


def get_guid(*, fd: Optional[int] = None, path: Optional[Path] = None) -> uuid.UUID:
    """Get the GUID of a disk image.

    One of ``fd`` or ``path`` must be given.

    :param fd: Readable file-descriptor to an image file
    :param path: Path of a readable image file

    :returns: GUID of the disk image

    .. versionadded:: 0.0.9
    """
    _check_fd_or_path(fd, path)

    with gptsum.gpt.GPTImage(fd=fd, path=path, open_mode=os.O_RDONLY) as image:
        image.validate()
        primary = image.read_primary_gpt_header()
        return primary.disk_guid


def set_guid(
    guid: uuid.UUID, *, fd: Optional[int] = None, path: Optional[Path] = None
) -> None:
    """Set the GUID of a disk image.

    One of ``fd`` or ``path`` must be given.

    :param guid: GUID to write to the disk image
    :param fd: Readable and writable file-descriptor to an image file
    :param path: Path of a readable and writable image file

    .. versionadded:: 0.0.9
    """
    _check_fd_or_path(fd, path)

    with gptsum.gpt.GPTImage(fd=fd, path=path, open_mode=os.O_RDWR) as image:
        image.validate()
        image.update_guid(guid)


def calculate_expected_guid(
    *, fd: Optional[int] = None, path: Optional[Path] = None
) -> uuid.UUID:
    """Calculate the expected checksum GUID of a disk image.

    One of ``fd`` or ``path`` must be given.

    :param fd: Readable file-descriptor to an image file
    :param path: Path of a readable image file

    :returns: Expected checksum GUID of the disk image

    .. versionadded:: 0.0.9
    """
    _check_fd_or_path(fd, path)

    with gptsum.gpt.GPTImage(fd=fd, path=path, open_mode=os.O_RDONLY) as image:
        image.validate()
        digest = gptsum.checksum.calculate(image)
        return gptsum.checksum.digest_to_guid(digest)


def embed(*, fd: Optional[int] = None, path: Optional[Path] = None) -> None:
    """Embed the calculated checksum GUID in an image file.

    In essence a combination of :func:`calculate_expected_guid` and :func:`set_guid`.

    One of ``fd`` or ``path`` must be given.

    :param fd: Readable and writable file-descriptor to an image file
    :param path: Path to a readable and writable image file

    .. versionadded:: 0.0.9
    """
    _check_fd_or_path(fd, path)

    current_guid = get_guid(fd=fd, path=path)
    checksum_guid = calculate_expected_guid(fd=fd, path=path)

    if current_guid != checksum_guid:
        set_guid(checksum_guid, fd=fd, path=path)


@dataclasses.dataclass(frozen=True)
class VerificationFailure(Exception):
    """Exception raised when :func:`verify` fails.

    .. versionadded:: 0.0.9
    """

    expected: uuid.UUID
    actual: uuid.UUID


def verify(*, fd: Optional[int] = None, path: Optional[Path] = None) -> None:
    """Verify a GPT disk image GUID against the calculated checksum.

    In essence a combination of :func:`calculate_expected_guid` and :func:`get_guid`.

    One of ``fd`` or ``path`` must be given.

    :param fd: Readable file-descriptor to an image file
    :param path: Path to a readable image file

    :raises VerificationFailure: Current GUID and checksum mismatch

    .. versionadded:: 0.0.9
    """
    _check_fd_or_path(fd, path)

    current_guid = get_guid(fd=fd, path=path)
    checksum_guid = calculate_expected_guid(fd=fd, path=path)

    if current_guid != checksum_guid:
        raise VerificationFailure(checksum_guid, current_guid)
