"""Tests for the :mod:`gptsum.gpt` module."""

import os
import struct
import tempfile
import uuid
from pathlib import Path
from typing import Iterator, Type

import pytest

from gptsum import gpt
from tests import conftest


@pytest.mark.parametrize(
    "header",
    [
        b"",
        b"\0",
        b"\0" * (gpt.LBA_SIZE - 1),
        b"\0" * (gpt.LBA_SIZE + 1),
    ],
)
def test_gptheader_unpack_invalid_header_size(header: bytes) -> None:
    """Test unpacking GPT headers of invalid size."""
    with pytest.raises(gpt.InvalidHeaderSizeError):
        gpt.GPTHeader.unpack(header)


# Generated using:
# $ truncate -s1G disk
# $ sfdisk disk << EOF
# label: gpt
# label-id: 97fe4bef-3385-45d8-becf-e0e178e0d1d9
# first-lba: 2048
# EOF
# Then, peel out bytes [512, 1024[ and [1024 * 1024 * 1024 - 512, 1024 * 1024 * 1024[
TEST_DISK_SIZE = 1024 * 1024 * 1024
TEST_DISK_UUID = uuid.UUID("97fe4bef-3385-45d8-becf-e0e178e0d1d9")
TEST_DISK_NUM_ENTRIES = 128
TEST_DISK_ENTRY_SIZE = 128
TEST_DISK_GPT_HEADER = (
    b"EFI PART\x00\x00\x01\x00\\\x00\x00\x00\xf9\xc2\x1d\x95\x00\x00\x00\x00\x01\x00"
    b"\x00\x00\x00\x00\x00\x00\xff\xff\x1f\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00"
    b"\x00\x00\x00\xde\xff\x1f\x00\x00\x00\x00\x00\xefK\xfe\x97\x853\xd8E\xbe\xcf\xe0"
    b"\xe1x\xe0\xd1\xd9\x02\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x80\x00\x00"
    b"\x00\x86\xd2T\xab\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00"
)
TEST_DISK_BACKUP_GPT_HEADER = (
    b"EFI PART\x00\x00\x01\x00\\\x00\x00\x00%\xb3\xe7\r\x00\x00\x00\x00\xff\xff\x1f"
    b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00"
    b"\x00\x00\xde\xff\x1f\x00\x00\x00\x00\x00\xefK\xfe\x97\x853\xd8E\xbe\xcf\xe0\xe1x"
    b"\xe0\xd1\xd9\xdf\xff\x1f\x00\x00\x00\x00\x00\x80\x00\x00\x00\x80\x00\x00\x00\x86"
    b"\xd2T\xab\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00"
)


@pytest.mark.parametrize(
    ("raw_header", "current_lba", "backup_lba", "entries_starting_lba"),
    [
        (TEST_DISK_GPT_HEADER, 1, TEST_DISK_SIZE // 512 - 1, 2),
        (
            TEST_DISK_BACKUP_GPT_HEADER,
            TEST_DISK_SIZE // 512 - 1,
            1,
            TEST_DISK_SIZE // 512
            - 1
            - (TEST_DISK_NUM_ENTRIES * TEST_DISK_ENTRY_SIZE // 512),
        ),
    ],
)
def test_gptheader_unpack(
    raw_header: bytes, current_lba: int, backup_lba: int, entries_starting_lba: int
) -> None:
    """Test unpacking of a valid GPT header."""
    header = gpt.GPTHeader.unpack(raw_header)

    assert header.current_lba == current_lba
    assert header.backup_lba == backup_lba
    assert header.first_usable_lba == 2048
    assert header.last_usable_lba == 2097118
    assert header.disk_guid == TEST_DISK_UUID
    assert header.entries_starting_lba == entries_starting_lba
    assert header.num_entries == TEST_DISK_NUM_ENTRIES
    assert header.entry_size == TEST_DISK_ENTRY_SIZE

    # Alternative, calculated way to find the right values
    assert (
        header.last_usable_lba
        == TEST_DISK_SIZE // 512
        - 1
        - (header.num_entries * header.entry_size // 512)
        - 1
    )


def _replace_signature(raw_header: bytes, signature: bytes) -> bytes:
    """Replace the 'signature' field in a raw header."""
    return signature + raw_header[8:]


def _replace_revision(raw_header: bytes, revision: bytes) -> bytes:
    """Replace the 'revision' field in a raw header."""
    return raw_header[:8] + revision + raw_header[8 + 4 :]


def _replace_header_size(raw_header: bytes, header_size: int) -> bytes:
    """Replace the 'header_size' field in a raw header."""
    header_size_bytes = struct.pack("<I", header_size)
    return raw_header[: 8 + 4] + header_size_bytes + raw_header[8 + 4 + 4 :]


def _replace_reserved(raw_header: bytes, reserved: bytes) -> bytes:
    """Replace the 'reserved' field in a raw header."""
    return raw_header[: 8 + 4 + 4 + 4] + reserved + raw_header[8 + 4 + 4 + 4 + 4 :]


def _replace_padding(raw_header: bytes, padding: bytes) -> bytes:
    """Replace the 'padding' field in a raw header."""
    return raw_header[:92] + padding


def _replace_header_crc32(raw_header: bytes, header_crc32: int) -> bytes:
    """Replace the 'header_crc32' field in a raw header."""
    header_crc32_bytes = struct.pack("<I", header_crc32)
    return raw_header[: 8 + 4 + 4] + header_crc32_bytes + raw_header[8 + 4 + 4 + 4 :]


@pytest.mark.parametrize(
    ("expected_error", "raw_header"),
    [
        (
            gpt.InvalidSignatureError,
            _replace_signature(TEST_DISK_GPT_HEADER, b"FFI PART"),
        ),
        (
            gpt.UnsupportedRevisionError,
            _replace_revision(TEST_DISK_GPT_HEADER, b"\0\0\1\1"),
        ),
        (gpt.InvalidHeaderSizeError, _replace_header_size(TEST_DISK_GPT_HEADER, 90)),
        (gpt.InvalidFieldError, _replace_reserved(TEST_DISK_GPT_HEADER, b"\0\0\0\1")),
        (
            gpt.InvalidFieldError,
            _replace_padding(TEST_DISK_GPT_HEADER, b"\1" * (512 - 92)),
        ),
        (
            gpt.HeaderChecksumMismatchError,
            _replace_header_crc32(TEST_DISK_GPT_HEADER, 2 ** 32 - 1),
        ),
    ],
)
def test_gptheader_unpack_error(
    expected_error: Type[Exception], raw_header: bytes
) -> None:
    """Test :meth:`gpt.GPTHeader.unpack` failure cases."""
    with pytest.raises(expected_error):
        gpt.GPTHeader.unpack(raw_header)


def test_gptheader_is_backup_of() -> None:
    """Test :meth:`gpt.GPTHeader.is_backup_of`."""
    gpt1 = gpt.GPTHeader.unpack(TEST_DISK_GPT_HEADER)
    gpt2 = gpt.GPTHeader.unpack(TEST_DISK_BACKUP_GPT_HEADER)

    assert gpt1.is_backup_of(gpt2)
    assert gpt2.is_backup_of(gpt1)

    assert not gpt1.is_backup_of(gpt1)
    assert not gpt2.is_backup_of(gpt2)


@pytest.mark.parametrize(
    "raw_header",
    [
        TEST_DISK_GPT_HEADER,
        TEST_DISK_BACKUP_GPT_HEADER,
    ],
)
def test_gptheader_pack(raw_header: bytes) -> None:
    """Test :meth:`gpt.GPTHeader.pack`."""
    assert gpt.GPTHeader.unpack(raw_header).pack() == raw_header


def test_gptheader_pack_override_crc32() -> None:
    """Test :meth:`gpt.GPTHeader.pack` overriding the CRC32."""
    header = gpt.GPTHeader.unpack(TEST_DISK_GPT_HEADER)
    packed = header.pack(override_crc32=0)
    with pytest.raises(gpt.HeaderChecksumMismatchError):
        gpt.GPTHeader.unpack(packed)


@pytest.fixture()
def small_file(tmp_path: Path) -> Iterator[Path]:
    """Yield the path of an empty, 1kB temporary file."""
    with tempfile.NamedTemporaryFile(dir=tmp_path) as tmp:
        tmp.truncate(1024)
        yield Path(tmp.name)


def test_gptimage_constructor(small_file: Path) -> None:
    """Test the :class:`gpt.GPTImage` constructor."""
    with pytest.raises(ValueError, match="Either fd or path must be given"):
        gpt.GPTImage()

    with pytest.raises(ValueError, match="Both fd and path can't be given"):
        gpt.GPTImage(fd=0, path=small_file)


def test_gptimage_too_small(small_file: Path) -> None:
    """Test :class:`gpt.GPTImage` with a (too) small file."""
    with open(small_file, "rb") as fd:
        with pytest.raises(gpt.InvalidImageError):  # noqa: PT012
            with gpt.GPTImage(fd=fd.fileno()):
                pytest.fail("This code should not be reached")  # pragma: no cover

    with pytest.raises(gpt.InvalidImageError):  # noqa: PT012
        with gpt.GPTImage(path=small_file):
            pytest.fail("This code should not be reached")  # pragma: no cover


def test_gptimage_validate() -> None:
    """Test :meth:`gpt.GPTImage.validate`."""
    with gpt.GPTImage(path=conftest.TESTDATA_DISK, open_mode=os.O_RDONLY) as image:
        image.validate()

    with open(conftest.TESTDATA_DISK, "rb") as fd:
        with gpt.GPTImage(fd=fd.fileno()) as image:
            image.validate()


def test_gptimage_validate_invalid_image(disk_image: Path) -> None:
    """Test :meth:`gpt.GPTImage.validate` with an invalid image."""
    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        primary = image.read_primary_gpt_header()

    new_guid = uuid.UUID("21da705c-fec8-4857-8379-449d823a7155")
    new_primary = gpt.GPTHeader(
        primary.current_lba,
        primary.backup_lba,
        primary.first_usable_lba,
        primary.last_usable_lba,
        new_guid,
        primary.entries_starting_lba,
        primary.num_entries,
        primary.entry_size,
        primary.entries_crc32,
    )

    with open(disk_image, "rb+") as fd:
        gpt.pwrite_all(fd.fileno(), new_primary.pack(), gpt.MBR_SIZE)

    with pytest.raises(gpt.InvalidImageError):  # noqa: PT012
        with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
            image.validate()


def test_gptimage_read_primary_gpt_header() -> None:
    """Test :meth:`gpt.GPTImage.read_primary_gpt_header`."""
    with gpt.GPTImage(path=conftest.TESTDATA_DISK, open_mode=os.O_RDONLY) as image:
        header = image.read_primary_gpt_header()
        assert header.disk_guid == conftest.TESTDATA_DISK_GUID
        assert header.first_usable_lba == 2048
        assert header.last_usable_lba == 4062
        assert header.current_lba == 1
        assert header.backup_lba == 4095


def test_gptimage_read_backup_gpt_header() -> None:
    """Test :meth:`gpt.GPTImage.read_backup_gpt_header`."""
    with gpt.GPTImage(path=conftest.TESTDATA_DISK, open_mode=os.O_RDONLY) as image:
        header = image.read_backup_gpt_header()
        assert header.disk_guid == conftest.TESTDATA_DISK_GUID
        assert header.first_usable_lba == 2048
        assert header.last_usable_lba == 4062
        assert header.current_lba == 4095
        assert header.backup_lba == 1


def test_gptimage_write_gpt_headers(disk_image: Path) -> None:
    """Test :meth:`gpt.GPTImage.write_gpt_headers`."""
    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        primary = image.read_primary_gpt_header()
        backup = image.read_backup_gpt_header()

    new_guid = uuid.UUID("086991f8-75bd-4560-8943-e11c0c59422b")

    new_primary = gpt.GPTHeader(
        primary.current_lba,
        primary.backup_lba,
        primary.first_usable_lba,
        primary.last_usable_lba,
        new_guid,
        primary.entries_starting_lba,
        primary.num_entries,
        primary.entry_size,
        primary.entries_crc32,
    )
    new_backup = gpt.GPTHeader(
        backup.current_lba,
        backup.backup_lba,
        backup.first_usable_lba,
        backup.last_usable_lba,
        new_guid,
        backup.entries_starting_lba,
        backup.num_entries,
        backup.entry_size,
        backup.entries_crc32,
    )

    with gpt.GPTImage(path=disk_image, open_mode=os.O_WRONLY) as image:
        image.write_gpt_headers(new_primary, new_backup)

    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        image.validate()
        assert image.read_primary_gpt_header().disk_guid == new_guid


def test_gptimage_write_gpt_headers_incompatible_headers(disk_image: Path) -> None:
    """Test :meth:`gpt.GPTImage.write_gpt_headers` with incompatible headers."""
    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        primary = image.read_primary_gpt_header()
        backup = image.read_backup_gpt_header()

        new_guid = uuid.UUID("913ef501-b10c-4fa4-8919-0d47f7d4d4bd")

        new_primary = gpt.GPTHeader(
            primary.current_lba,
            primary.backup_lba,
            primary.first_usable_lba,
            primary.last_usable_lba,
            new_guid,
            primary.entries_starting_lba,
            primary.num_entries,
            primary.entry_size,
            primary.entries_crc32,
        )

        with pytest.raises(
            ValueError, match="Given headers are not backups of each other"
        ):
            image.write_gpt_headers(new_primary, backup)


def test_gptimage_write_gpt_headers_incorrect_current_lba(disk_image: Path) -> None:
    """Test :meth:`gpt.GPTImage.write_gpt_headers` with incorrect headers."""
    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        primary = image.read_primary_gpt_header()
        backup = image.read_backup_gpt_header()

        with pytest.raises(
            ValueError, match="Primary header has invalid 'current_lba', expected 1"
        ):
            image.write_gpt_headers(backup, primary)

        with open(disk_image, "rb+") as fd:
            size = os.fstat(fd.fileno()).st_size
            fd.truncate(size + gpt.LBA_SIZE)

        with pytest.raises(
            ValueError, match=r"Backup header has invalid 'current_lba', expected \d+"
        ):
            image.write_gpt_headers(primary, backup)


def test_gptimage_update_guid(disk_image: Path) -> None:
    """Test :meth:`gpt.GPTImage.update_guid`."""
    new_guid = uuid.UUID("910fbf4b-f2ac-4d2c-8995-9dff42b9efde")

    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDWR) as image:
        image.update_guid(new_guid)

    with gpt.GPTImage(path=disk_image, open_mode=os.O_RDONLY) as image:
        image.validate()
        assert image.read_primary_gpt_header().disk_guid == new_guid
        assert image.read_backup_gpt_header().disk_guid == new_guid
