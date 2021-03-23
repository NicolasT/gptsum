gptsum
======
A tool to make disk images using GPT_ partitions self-verifiable, like
`isomd5sum`_.

Note this *only* works for read-only, immutable images!

.. _GPT: https://en.wikipedia.org/wiki/GUID_Partition_Table
.. _isomd5sum: https://github.com/rhinstaller/isomd5sum

Quickstart
**********
.. When making changes to the quickstart code below,
   make sure 'tests/test_readme.py' is updated accordingly.

First, create an empty disk image::

    $ truncate -s64M image.raw

Then, create a GPT partition table in it. Note, below we set an explicit
`label-id`. In general, this should not be done and a random GUID will be
generated. Simply remove the line.

::

    $ sfdisk image.raw << EOF
    label: gpt
    label-id: 132e3631-1ec9-4411-ab25-9b95b54b0903
    first-lba: 2048
    EOF

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

We can retrieve the current disk GUID using ``gptsum``::

    $ gptsum get-guid image.raw
    132e3631-1ec9-4411-ab25-9b95b54b0903

Verification should fail::

    $ gptsum verify image.raw || echo "Verification failed!"
    Disk GUID doesn't match expected checksum, got 132e3631-1ec9-4411-ab25-9b95b54b0903, expected 6190f5bb-1967-14ec-9fbd-a7d213a45461
    Verification failed!

Embed the disk checksum as the label GUID::

    $ gptsum embed image.raw

Verification should now succeed::

    $ gptsum verify image.raw && echo "Verification succeeded!"
    Verification succeeded!

Indeed, the GUID was changed::

    $ gptsum get-guid image.raw
    6190f5bb-1967-14ec-9fbd-a7d213a45461


How It Works
************
Generally, when checksums are used to validate the integrity of a file, this
checksum needs to be provided out-of-band, e.g., in a separate file. This
complicates the process a bit, since now multiple files need to be kept around
(and potentially in sync).

Being able to verify a file's integrity without any external information would
be great. However, if we embed the checksum of a file in the file itself, we
change its checksum and verification would fail. So we need to apply some
tricks.

The `isomd5sum`_ tool is often used to verify the integrity of ISO files, e.g.,
Linux distribution releases. It uses an unused location in the ISO9660 file
format to embed an MD5 checksum of the actual data segments of said file. As
such, this MD5 checksum does not represent the complete file contents but only
the pieces of data we're interested in.

We can translate this to GPT-partitioned disk images as well. In the GPT
format, there's no room to embed any arbitrary blobs (unless we'd use the
reserved or padding sections of the headers, which should be zeroed out so we
shouldn't). However, GPT disks are identified by a GUID which is stored in the
two metadata sections stored on the disk, at LBA 1 and as the last LBA on the
disk (the so-called primary and secondary GPT headers). This leaves room for 16
bytes of semi-arbitrary data.

Furthermore, the GPT headers themselves, including the GUID, are protected
using a CRC32 checksum.

As such, we can apply the following procedure:

- Zero out the CRC32 and GUID fields in both GPT headers
- Calculate a 16 byte checksum of the resulting image (covering all data,
  except for the CRC32 and GUID fields)
- Embed the checksum as the GUID field in both GPT headers (now becoming the
  disk GUID)
- Update the CRC32 fields in both GPT headers

At this point we have a fully valid GPT disk image with a GUID representing
the actual data contained in the image. One could argue this is no longer a
valid GUID (indeed it's not), but since it's generated using a secure hashing
algorithm over a (potentially large) file, we can assume the entropy is
sufficient to avoid collisions. Essentially, if two disk images were to get the
same GUID, they're very likely the exact same disk image, content-wise.

Verifying an image file is roughly the same procedure:

- Zero out the CRC32 and GUID fields in both GPT headers (in-memory)
- Calculate a 16 byte checksum of the resulting image
- Verify this calculated checksum equals the actual GUID embedded in the image

Implementation Details
**********************
`gptsum` is implemented in Python, and compatible with Python 3.6 and later.
It uses the `Blake2b`_ checksum algorithm to construct a 16 byte digest
of the disk image.

Various subcommands are exposed by the CLI, refer to the `documentation`_
for more details.

.. _Blake2b: https://en.wikipedia.org/wiki/BLAKE_(hash_function)#BLAKE2
.. _documentation: https://nicolast.github.io/gptsum/
