"""Test code from `README.rst`."""

import shutil
import subprocess  # noqa: S404
from pathlib import Path
from typing import Optional

import pytest


@pytest.mark.skipif(shutil.which("sfdisk") is None, reason="sfdisk not found")
def test_quickstart(tmp_path: Path) -> None:
    """Run the 'Quickstart' section from 'README.rst'."""

    def check_call(cmd: bytes) -> None:
        subprocess.check_call(
            args=[cmd],
            shell=True,
            cwd=tmp_path,
        )

    def check_output(cmd: bytes, input_: Optional[bytes] = None) -> bytes:
        return subprocess.check_output(
            args=[cmd],
            shell=True,
            cwd=tmp_path,
            input=input_ or b"",
            stderr=subprocess.STDOUT,
        )

    check_call(b"truncate -s64M image.raw")

    sfdisk_input = b"""
label: gpt
label-id: 132e3631-1ec9-4411-ab25-9b95b54b0903
first-lba: 2048
"""
    expected_sfdisk_output = b"""\
Checking that no-one is using this disk right now ... OK

Disk image.raw: 64 MiB, 67108864 bytes, 131072 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes

>>> Script header accepted.
>>> Script header accepted.
>>> Script header accepted.
>>> Done.
Created a new GPT disklabel (GUID: 132E3631-1EC9-4411-AB25-9B95B54B0903).

New situation:
Disklabel type: gpt
Disk identifier: 132E3631-1EC9-4411-AB25-9B95B54B0903

The partition table has been altered.
Syncing disks.
"""
    assert (
        check_output(b"sfdisk image.raw", input_=sfdisk_input) == expected_sfdisk_output
    )

    assert (
        check_output(b"gptsum get-guid image.raw")
        == b"132e3631-1ec9-4411-ab25-9b95b54b0903\n"
    )

    assert check_output(b'gptsum verify image.raw || echo "Verification failed!"') == (
        b"Disk GUID doesn't match expected checksum, "
        b"got 132e3631-1ec9-4411-ab25-9b95b54b0903, "
        b"expected 6190f5bb-1967-14ec-9fbd-a7d213a45461\n"
        b"Verification failed!\n"
    )

    check_call(b"gptsum embed image.raw")

    assert (
        check_output(b'gptsum verify image.raw && echo "Verification succeeded!"')
        == b"Verification succeeded!\n"
    )

    assert (
        check_output(b"gptsum get-guid image.raw")
        == b"6190f5bb-1967-14ec-9fbd-a7d213a45461\n"
    )
