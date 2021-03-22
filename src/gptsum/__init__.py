"""
gptsum: a tool to make disk images using GPT partitions self-verifiable.

Like `isomd5sum <https://github.com/rhinstaller/isomd5sum>`_.
"""

from typing import cast

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # type: ignore


__version__: str = cast(str, importlib_metadata.version(__name__))  # type: ignore
