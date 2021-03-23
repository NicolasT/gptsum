"""Code to work with `GPT`_ images and headers.

.. _GPT: https://en.wikipedia.org/wiki/GUID_Partition_Table
"""

import binascii
import dataclasses
import os
import struct
import uuid
from pathlib import Path
from types import TracebackType
from typing import ContextManager, Optional, Type

LBA_SIZE = 512
MBR_SIZE = LBA_SIZE
GPT_HEADER_SIZE = LBA_SIZE

_EXPECTED_ACTUAL_HEADER_SIZE = 92
_EXPECTED_PADDING_SIZE = GPT_HEADER_SIZE - _EXPECTED_ACTUAL_HEADER_SIZE

_GPT_ACTUAL_HEADER_STRUCT_FORMAT = "<8s4sII4sQQQQ16sQIII"
_GPT_ACTUAL_HEADER_STRUCT = struct.Struct(_GPT_ACTUAL_HEADER_STRUCT_FORMAT)
assert _GPT_ACTUAL_HEADER_STRUCT.size == _EXPECTED_ACTUAL_HEADER_SIZE  # noqa: S101
_GPT_HEADER_STRUCT = struct.Struct(
    "{}{}s".format(_GPT_ACTUAL_HEADER_STRUCT_FORMAT, _EXPECTED_PADDING_SIZE)
)
assert _GPT_HEADER_STRUCT.size == GPT_HEADER_SIZE  # noqa: S101

_EXPECTED_SIGNATURE = b"EFI PART"
_EXPECTED_REVISION = b"\0\0\1\0"
_EXPECTED_RESERVED = b"\0" * 4
_EXPECTED_PADDING = b"\0" * _EXPECTED_PADDING_SIZE


class GPTError(Exception):
    """Generic GPT error."""


class InvalidHeaderSizeError(ValueError, GPTError):
    """Header of invalid size passed in."""


class InvalidFieldError(ValueError, GPTError):
    """A GPT header field has invalid contents."""


class InvalidSignatureError(InvalidFieldError):
    """Invalid signature found in header."""


class UnsupportedRevisionError(ValueError, GPTError):
    """GPT header of unsupported revision passed in."""


class HeaderChecksumMismatchError(ValueError, GPTError):
    """GPT header checksum mismatch."""


class InvalidImageError(ValueError, GPTError):
    """A file which is supposedly a GPT image is not."""


@dataclasses.dataclass(frozen=True)
class GPTHeader(object):
    """Representation of a GPT header."""

    current_lba: int
    backup_lba: int
    first_usable_lba: int
    last_usable_lba: int
    disk_guid: uuid.UUID
    entries_starting_lba: int
    num_entries: int
    entry_size: int
    entries_crc32: int

    @classmethod
    def unpack(cls, raw_header: bytes) -> "GPTHeader":
        """Unpack a GPT header from its raw encoding.

        The given raw header must include all padding, i.e., its length must be
        512 bytes.

        :param raw_header: Raw GPT header
        :type raw_header: bytes

        :return: A :class:`GPTHeader` instance representing the raw GPT header
        :rtype: GPTHeader

        :raises InvalidHeaderSizeError: Given `raw_header` has invalid length
        :raises InvalidSignatureError: Invalid GPT signature in raw header
        :raises UnsupportedRevisionError: Unsupported GPT revision
        :raises InvalidFieldError: Invalid GPT field value detected
        :raises HeaderChecksumMismatchError: Header checksum mismatch detected
        """
        if len(raw_header) != GPT_HEADER_SIZE:
            raise InvalidHeaderSizeError(
                "Not a valid GPT header, must be {} bytes".format(GPT_HEADER_SIZE)
            )

        (
            signature,
            revision,
            header_size,
            header_crc32,
            reserved,
            current_lba,
            backup_lba,
            first_usable_lba,
            last_usable_lba,
            disk_guid,
            entries_starting_lba,
            num_entries,
            entry_size,
            entries_crc32,
            padding,
        ) = _GPT_HEADER_STRUCT.unpack(raw_header)

        if signature != _EXPECTED_SIGNATURE:
            raise InvalidSignatureError(
                "Not a valid GPT header, signature must be {}".format(
                    _EXPECTED_SIGNATURE.decode("ascii")
                )
            )

        if revision != _EXPECTED_REVISION:
            raise UnsupportedRevisionError("Unsupported GPT revision")

        if header_size != _EXPECTED_ACTUAL_HEADER_SIZE:
            raise InvalidHeaderSizeError(
                "GPT header is supposedly {} bytes long, expected {}".format(
                    header_size, _EXPECTED_ACTUAL_HEADER_SIZE
                )
            )

        header = raw_header[:header_size]

        if reserved != _EXPECTED_RESERVED:
            raise InvalidFieldError("GPT 'reserved' field has unexpected contents")

        if padding != _EXPECTED_PADDING:
            raise InvalidFieldError("GPT header padding has unexpected contents")

        prefix_crc32 = binascii.crc32(header[: 8 + 4 + 4])
        with_zeroed_crc32_crc32 = binascii.crc32(b"\0" * 4, prefix_crc32)
        calculated_header_crc32 = binascii.crc32(
            header[8 + 4 + 4 + 4 :], with_zeroed_crc32_crc32
        )
        calculated_header_crc32 &= 0xFFFFFFFF

        if header_crc32 != calculated_header_crc32:
            raise HeaderChecksumMismatchError(
                "GPT header CRC32 mismatch, got {}, expected {}".format(
                    calculated_header_crc32, header_crc32
                )
            )

        return cls(
            current_lba,
            backup_lba,
            first_usable_lba,
            last_usable_lba,
            uuid.UUID(bytes_le=disk_guid),
            entries_starting_lba,
            num_entries,
            entry_size,
            entries_crc32,
        )

    def pack(self, override_crc32: Optional[int] = None) -> bytes:
        """Pack the header in its raw bytes serialized form.

        :param override_crc32: Use the given value as CRC32 instead of calculating it

        :return: Serialized representation of the GPT header
        :rtype: bytes
        """
        if override_crc32 is not None:
            header_crc32 = override_crc32
        else:
            header_with_zero_crc32 = _GPT_ACTUAL_HEADER_STRUCT.pack(
                _EXPECTED_SIGNATURE,
                _EXPECTED_REVISION,
                _EXPECTED_ACTUAL_HEADER_SIZE,
                0,
                _EXPECTED_RESERVED,
                self.current_lba,
                self.backup_lba,
                self.first_usable_lba,
                self.last_usable_lba,
                self.disk_guid.bytes_le,
                self.entries_starting_lba,
                self.num_entries,
                self.entry_size,
                self.entries_crc32,
            )
            header_crc32 = binascii.crc32(header_with_zero_crc32)

        return _GPT_HEADER_STRUCT.pack(
            _EXPECTED_SIGNATURE,
            _EXPECTED_REVISION,
            _EXPECTED_ACTUAL_HEADER_SIZE,
            header_crc32,
            _EXPECTED_RESERVED,
            self.current_lba,
            self.backup_lba,
            self.first_usable_lba,
            self.last_usable_lba,
            self.disk_guid.bytes_le,
            self.entries_starting_lba,
            self.num_entries,
            self.entry_size,
            self.entries_crc32,
            _EXPECTED_PADDING,
        )

    def is_backup_of(self, other: "GPTHeader") -> bool:
        """Check whether the given GPT header is a backup of this one."""
        return all(
            [
                self.current_lba == other.backup_lba,
                self.backup_lba == other.current_lba,
                self.first_usable_lba == other.first_usable_lba,
                self.last_usable_lba == other.last_usable_lba,
                self.disk_guid == other.disk_guid,
                self.num_entries == other.num_entries,
                self.entry_size == other.entry_size,
                self.entries_crc32 == other.entries_crc32,
            ]
        )

    def with_new_guid(self, new_guid: uuid.UUID) -> "GPTHeader":
        """Construct a copy of the GPT header with a new GUID."""
        return GPTHeader(
            self.current_lba,
            self.backup_lba,
            self.first_usable_lba,
            self.last_usable_lba,
            new_guid,
            self.entries_starting_lba,
            self.num_entries,
            self.entry_size,
            self.entries_crc32,
        )


def pread_all(fd: int, size: int, offset: int) -> bytes:
    """Use :func:`os.pread` to read data, handling partial reads."""
    pieces = []
    while size > 0:
        read = os.pread(fd, size, offset)
        pieces.append(read)
        len_read = len(read)
        size -= len_read
        offset += len_read
    return b"".join(pieces)


def pwrite_all(fd: int, data: bytes, offset: int) -> None:
    """Use :func:`os.pwrite` to write data, handling partial writes."""
    while len(data) != 0:
        written = os.pwrite(fd, data, offset)
        data = data[written:]
        offset += written


class GPTImage(ContextManager["GPTImage"]):
    """Wrapper around a GPT-partitioned disk image file."""

    def __init__(
        self,
        *,
        fd: Optional[int] = None,
        path: Optional[Path] = None,
        open_mode: int = os.O_RDWR,
    ):
        """Construct a new :class:`GPTImage`.

        :param fd: File descriptor to open image file
        :param path: Path to image file to use
        :param open_mode: Mode to use when opening the disk image file

        :raises ValueError: Both or none of `fd` and `path` are provided
        """
        if fd is None and path is None:
            raise ValueError("Either fd or path must be given")

        if fd is not None and path is not None:
            raise ValueError("Both fd and path can't be given")

        self._fd = fd
        self._path = path
        self._open_mode = open_mode

    def fileno(self) -> int:
        """Get a file descriptor for the image file.

        :returns: FD to the image file

        :raises RuntimeError: No open FD to the image
        """
        if self._fd is None:
            raise RuntimeError("No open file descriptor")  # pragma: no cover

        return self._fd

    def __enter__(self) -> "GPTImage":
        """Open the disk image for use in a context.

        If `fd` was passed during construction, nothing happens, and the FD won't be
        closed by `__exit__`.

        :returns: `self`

        :raises InvalidImageError: File is not a valid GPT image
        """
        if self._fd is None:
            assert self._path is not None  # noqa: S101
            self._fd = os.open(
                self._path, os.O_CLOEXEC | os.O_LARGEFILE | self._open_mode
            )

        if os.fstat(self._fd).st_size < MBR_SIZE + GPT_HEADER_SIZE + GPT_HEADER_SIZE:
            if self._path is not None:
                os.close(self._fd)
                self._fd = None
            raise InvalidImageError("Image file too small to be a valid GPT image")

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close the disk image when exiting a context."""
        if self._path is not None and self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def _read_gpt_header(self, offset: int) -> GPTHeader:
        if self._fd is None:
            raise RuntimeError("No open file descriptor")  # pragma: no cover
        raw_header = pread_all(self._fd, GPT_HEADER_SIZE, offset)
        return GPTHeader.unpack(raw_header)

    def read_primary_gpt_header(self) -> GPTHeader:
        """Read the primary GPT header from the image."""
        return self._read_gpt_header(MBR_SIZE)

    def read_backup_gpt_header(self) -> GPTHeader:
        """Read the backup GPT header from the image."""
        if self._fd is None:
            raise RuntimeError("No open file descriptor")  # pragma: no cover
        size = os.fstat(self._fd).st_size
        return self._read_gpt_header(size - GPT_HEADER_SIZE)

    def validate(self) -> None:
        """Validate the GPT headers found in the image.

        :raises InvalidImageError: GPT headers are not compatible
        """
        gpt1 = self.read_primary_gpt_header()
        gpt2 = self.read_backup_gpt_header()

        if not gpt2.is_backup_of(gpt1) or not gpt1.is_backup_of(gpt2):
            raise InvalidImageError("GPT headers don't match")

    def write_gpt_headers(self, primary: GPTHeader, backup: GPTHeader) -> None:
        """Write primary and backup GPT headers to the image.

        :param primary: Primary GPT header to write
        :param backup: Backup GPT header to write

        :raises RuntimeError: No open file descriptor
        :raises ValueError: Given headers are not backups of each other
        :raises ValueError: Primary header has invalid 'current_lba'
        :raises ValueError: Backup header has invalid 'current_lba'
        """
        if self._fd is None:
            raise RuntimeError("No open file descriptor")  # pragma: no cover

        if not backup.is_backup_of(primary) or not primary.is_backup_of(backup):
            raise ValueError("Given headers are not backups of each other")

        if primary.current_lba != 1:
            raise ValueError("Primary header has invalid 'current_lba', expected 1")

        size = os.fstat(self._fd).st_size
        expected_backup_lba = size // 512 - 1
        if backup.current_lba != expected_backup_lba:
            raise ValueError(
                "Backup header has invalid 'current_lba', expected {}".format(
                    expected_backup_lba
                )
            )

        gpt1 = primary.pack()
        gpt2 = backup.pack()

        pwrite_all(self._fd, gpt1, primary.current_lba * LBA_SIZE)
        pwrite_all(self._fd, gpt2, backup.current_lba * LBA_SIZE)
        os.fsync(self._fd)

    def update_guid(self, guid: uuid.UUID) -> None:
        """Update the label GUID of the image to some new UUID.

        The new GPT headers are written to the image.

        :param guid: New label GUID to write to the disk image
        """
        primary = self.read_primary_gpt_header()
        backup = self.read_backup_gpt_header()

        new_primary = primary.with_new_guid(guid)
        new_backup = backup.with_new_guid(guid)

        self.write_gpt_headers(new_primary, new_backup)
