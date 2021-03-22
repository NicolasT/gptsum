"""Code to work with `GPT`_ images and headers.

.. _GPT: https://en.wikipedia.org/wiki/GUID_Partition_Table
"""

import binascii
import dataclasses
import struct
import uuid
from typing import Optional

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

        calculated_header_crc32 = (
            binascii.crc32(
                header[8 + 4 + 4 + 4 :],
                binascii.crc32(b"\0" * 4, binascii.crc32(header[: 8 + 4 + 4])),
            )
            & 0xFFFFFFFF
        )

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
