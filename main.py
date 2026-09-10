"""CLI entry point for the local Excel agent.

Usage:
    python main.py workbooks/example.xlsx
"""

from __future__ import annotations

import sys
from pathlib import Path

from agent import MaxStepsExceeded, run_agent


def _usage() -> None:
    print("Usage: python main.py <path/to/workbook.xlsx>")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        _usage()
        return 2

    workbook_path = Path(argv[0]).expanduser()
    if not workbook_path.exists():
        print(f"Error: workbook not found: {workbook_path}")
        return 1
    if workbook_path.suffix.lower() != ".xlsx":
        print(f"Error: expected an .xlsx file, got: {workbook_path.name}")
        return 1

    print(f"Excel agent ready. Editing: {workbook_path}")
    print("Type an instruction, or 'exit' to quit.\n")

    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if prompt.lower() in {"exit", "quit"}:
            return 0
        if not prompt:
            continue

        print("working...", flush=True)
        try:
            answer = run_agent(prompt, str(workbook_path))
        except MaxStepsExceeded as exc:
            print(f"\n[stopped] {exc}\n")
            continue
        except Exception as exc:  # noqa: BLE001 - CLI should not crash on one bad turn
            print(f"\n[error] {type(exc).__name__}: {exc}\n")
            continue

        print(f"\n{answer}\n")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
