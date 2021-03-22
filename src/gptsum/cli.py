"""gptsum CLI implementation."""

import argparse
from typing import List, Optional

import gptsum


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    description = (
        gptsum.__doc__.strip().splitlines()[0].split(":", 1)[1].strip().capitalize()
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--version", action="version", version=gptsum.__version__)

    return parser


def main(args: Optional[List[str]] = None) -> None:
    """Run the CLI program."""
    parser = build_parser()
    parser.parse_args(args)
