"""Central tool registry: schemas, dispatch and runtime validation."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError

import excel_tools
from schemas import (
    CreateSheetArgs,
    InspectWorkbookArgs,
    ReadRangeArgs,
    SaveWorkbookArgs,
    WriteFormulaArgs,
    WriteRangeArgs,
)

TOOLS: Dict[str, Dict[str, Any]] = {
    "inspect_workbook": {
        "description": (
            "Inspect the workbook structure: sheet names, dimensions, the first "
            "few rows of each sheet and detected headers. Call this before making "
            "assumptions about an unfamiliar workbook."
        ),
        "args_model": InspectWorkbookArgs,
        "function": excel_tools.inspect_workbook,
    },
    "read_range": {
        "description": (
            "Read values and formulas from a worksheet range in A1 notation. "
            "Returns each cell's coordinate, value and formula (when stored)."
        ),
        "args_model": ReadRangeArgs,
        "function": excel_tools.read_range,
    },
    "write_range": {
        "description": (
            "Write a 2D array of literal values into a sheet starting at a cell. "
            "Saves the workbook and returns the number of cells modified."
        ),
        "args_model": WriteRangeArgs,
        "function": excel_tools.write_range,
    },
    "write_formula": {
        "description": (
            "Write an Excel formula to a cell or range. For a range, the formula "
            "is filled down/across with references adjusted per cell. Preserves "
            "unrelated data and saves the workbook."
        ),
        "args_model": WriteFormulaArgs,
        "function": excel_tools.write_formula,
    },
    "create_sheet": {
        "description": (
            "Create a new worksheet. Rejects duplicate names. Saves the workbook."
        ),
        "args_model": CreateSheetArgs,
        "function": excel_tools.create_sheet,
    },
    "save_workbook": {
        "description": "Explicitly save the current workbook to disk.",
        "args_model": SaveWorkbookArgs,
        "function": excel_tools.save_workbook,
    },
}


def _json_schema(model: type[BaseModel]) -> Dict[str, Any]:
    schema = model.model_json_schema()
    # OpenAI rejects unresolved $defs / titles in some modes; keep it minimal.
    schema.pop("title", None)
    schema.setdefault("type", "object")
    schema.setdefault("properties", {})
    return schema


def get_tool_schemas() -> List[Dict[str, Any]]:
    """Return OpenAI-compatible function tool schemas for every registered tool."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": spec["description"],
                "parameters": _json_schema(spec["args_model"]),
            },
        }
        for name, spec in TOOLS.items()
    ]


def execute_tool(tool_call: Any, workbook_path: str) -> Dict[str, Any]:
    """Validate arguments, dispatch to the tool function and return a result dict.

    ``tool_call`` must expose ``name`` (str) and ``arguments`` (dict). Any failure
    is returned as ``{"success": False, "error": ...}`` so the model can recover.
    """
    name = getattr(tool_call, "name", None)
    raw_args = getattr(tool_call, "arguments", None) or {}

    spec = TOOLS.get(name)
    if spec is None:
        return {"success": False, "error": f"Unknown tool '{name}'."}

    if not isinstance(raw_args, dict):
        return {
            "success": False,
            "error": f"Tool arguments must be a JSON object, got {type(raw_args).__name__}.",
        }

    try:
        args = spec["args_model"](**raw_args)
    except ValidationError as exc:
        return {
            "success": False,
            "error": "Invalid arguments.",
            "validation_errors": exc.errors(include_url=False),
        }

    try:
        return spec["function"](workbook_path=workbook_path, **args.model_dump())
    except excel_tools.ExcelToolError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - surface unexpected errors to the model
        return {
            "success": False,
            "error": f"Unexpected {type(exc).__name__}: {exc}",
        }
