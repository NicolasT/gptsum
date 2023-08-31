"""Global definitions for pytest tests."""

import io
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator, cast

import pytest

TESTDATA_DISK = Path(__file__).parent / "testdata" / "disk"
TESTDATA_DISK_GUID = uuid.UUID("66E0318D-A103-9549-8583-80E8ABCD4CD8")

TESTDATA_EMBEDDED_DISK = Path(__file__).parent / "testdata" / "embedded-disk"
TESTDATA_EMBEDDED_DISK_GUID = uuid.UUID("D4750646-01FD-2608-959F-159017007377")


@pytest.fixture()
def disk_image(tmp_path: Path) -> Iterator[Path]:
    """Yield the path to a copy of `TESTDATA_DISK`."""
    with tempfile.NamedTemporaryFile(dir=tmp_path, delete=False) as tmp:
        with open(TESTDATA_DISK, "rb") as disk:
            if TYPE_CHECKING:  # pragma: no cover
                copyfileobj = cast(
                    Callable[
                        # pylint: disable=protected-access
                        [io.BufferedReader, tempfile._TemporaryFileWrapper[bytes]],
                        None,
                    ],
                    shutil.copyfileobj,
                )
            else:
                copyfileobj = shutil.copyfileobj

            copyfileobj(disk, tmp)

        tmp.close()
        yield Path(tmp.name)
