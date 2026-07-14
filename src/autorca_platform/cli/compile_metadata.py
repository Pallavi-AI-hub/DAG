"""CLI for compiling the architecture workbook into JSON metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

from autorca_platform.core.exceptions import AutoRCABaseException
from autorca_platform.metadata.compiler import MetadataCompiler


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="autorca-metadata",
        description="Compile AI AutoRCA architecture workbook metadata.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile workbook to JSON configs.")
    compile_parser.add_argument("--input", required=True, type=Path, help="Architecture .xlsx file.")
    compile_parser.add_argument("--output", required=True, type=Path, help="Output config directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the metadata CLI.

    Args:
        argv: Optional argument vector for tests.

    Returns:
        Process exit code.
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compile":
        try:
            compiled = MetadataCompiler().compile_to_directory(args.input, args.output)
        except AutoRCABaseException as exc:
            parser.exit(1, f"{exc}\n")
        print(  # noqa: T201
            f"Compiled {compiled.global_config.dag_count} DAG configs "
            f"and {compiled.global_config.task_count} task rows to {args.output}"
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
