"""gptsum CLI implementation."""

import argparse
import sys
import uuid
from typing import List, Optional

import gptsum
import gptsum.checksum
import gptsum.gpt


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    docstring_firstline = gptsum.__doc__.strip().splitlines()[0]
    docstring_suffix = docstring_firstline.split(":", 1)[1]
    description = docstring_suffix.strip().capitalize()
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--version", action="version", version=gptsum.__version__)

    subparsers = parser.add_subparsers(title="subcommands")

    embed_parser = subparsers.add_parser(
        "embed",
        help="calculate and embed the image checksum as its GUID",
        description="Calculate and embed the checksum of a disk image as its GUID.",
    )
    embed_parser.set_defaults(func=embed)
    embed_parser.add_argument(
        "image",
        type=argparse.FileType("rb+"),
        help="disk image file",
        metavar="FILE",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="verify disk image contents against the expected checksum (GUID)",
        description=(
            "Calculate the expected checksum of a disk image, "
            "then verify the embedded disk GUID against it. "
            "If there's a mismatch, the tool will exit with exit code 1."
        ),
    )
    verify_parser.set_defaults(func=verify)
    verify_parser.add_argument(
        "image",
        type=argparse.FileType("rb"),
        help="disk image file",
        metavar="FILE",
    )

    get_guid_parser = subparsers.add_parser(
        "get-guid",
        help="read a disk image GUID",
        description="Read and print the GPT label GUID from a disk image.",
    )
    get_guid_parser.set_defaults(func=get_guid)
    get_guid_parser.add_argument(
        "image",
        type=argparse.FileType("rb"),
        help="disk image file",
        metavar="FILE",
    )

    set_guid_parser = subparsers.add_parser(
        "set-guid",
        help="set a disk image GUID",
        description="Write a new label GUID to a disk image.",
    )
    set_guid_parser.set_defaults(func=set_guid)
    set_guid_parser.add_argument(
        "image",
        type=argparse.FileType("rb+"),
        help="disk image file",
        metavar="FILE",
    )
    set_guid_parser.add_argument(
        "guid",
        type=uuid.UUID,
        help="new label GUID",
        metavar="GUID",
    )

    calculate_guid_parser = subparsers.add_parser(
        "calculate-expected-guid",
        help="calculate and print the expected checksum (GUID) of an image",
        description=(
            "Calculate and print the expected checksum (GUID) of a disk image, "
            "without writing it to the file."
        ),
    )
    calculate_guid_parser.set_defaults(func=calculate_expected_guid)
    calculate_guid_parser.add_argument(
        "image",
        type=argparse.FileType("rb"),
        help="disk image file",
        metavar="FILE",
    )

    return parser


def get_guid(ns: argparse.Namespace) -> None:
    """Execute the 'get-guid' subcommand."""
    guid = gptsum.get_guid(fd=ns.image.fileno())
    print("{}".format(guid))


def set_guid(ns: argparse.Namespace) -> None:
    """Execute the 'set-guid' subcommand."""
    gptsum.set_guid(ns.guid, fd=ns.image.fileno())


def calculate_expected_guid(ns: argparse.Namespace) -> None:
    """Execute the 'calculate-expected-guid' subcommand."""
    guid = gptsum.calculate_expected_guid(fd=ns.image.fileno())
    print("{}".format(guid))


def embed(ns: argparse.Namespace) -> None:
    """Execute the 'embed' subcommand."""
    gptsum.embed(fd=ns.image.fileno())


def verify(ns: argparse.Namespace) -> None:
    """Execute the 'verify' subcommand."""
    try:
        gptsum.verify(fd=ns.image.fileno())
    except gptsum.VerificationFailure as exn:
        sys.stderr.write(
            "Disk GUID doesn't match expected checksum, "
            "got {}, expected {}\n".format(exn.actual, exn.expected)
        )
        sys.stderr.flush()
        sys.exit(1)


def main(args: Optional[List[str]] = None) -> None:
    """Run the CLI program."""
    parser = build_parser()
    ns = parser.parse_args(args)

    func = getattr(ns, "func", None)
    if func:
        func(ns)
    else:
        parser.print_usage()
