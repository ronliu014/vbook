"""Command-line interface for vBook."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from vbook_common.config import load_config
from vbook_common.serialization import to_jsonable
from vbook_common.version import __version__


def main(argv: Sequence[str] | None = None) -> int:
    """Run the vBook CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "check":
        print("vBook skeleton ready")
        return 0

    if args.command == "config":
        if args.show:
            print(json.dumps(to_jsonable(load_config()), ensure_ascii=False, indent=2))
            return 0
        parser.error("config requires --show")

    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vbook")
    parser.add_argument("--version", action="store_true", help="Print vBook version and exit")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check", help="Check skeleton readiness")

    config_parser = subparsers.add_parser("config", help="Inspect configuration")
    config_parser.add_argument("--show", action="store_true", help="Print resolved configuration")

    return parser
