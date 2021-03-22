testdata
========
These are some data files used by various tests.

`disk` is a disk image with a GPT label, created as-is. `embedded-disk` is a
copy of `disk` with the GPT label GUID set to the checksum of the disk data.
As such, `embedded-disk` is `disk` once `gptsum embed disk` has been called.
