"""Pydantic argument schemas for every agent tool.

These models are used both to generate JSON Schema for the LLM and to
validate tool-call arguments at runtime.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class InspectWorkbookArgs(BaseModel):
    """inspect_workbook takes no arguments."""

    model_config = {"extra": "forbid"}


class ReadRangeArgs(BaseModel):
    sheet: str = Field(description="Name of the worksheet to read")
    cell_range: str = Field(
        description="Excel range in A1 notation, for example A1:C10"
    )

    model_config = {"extra": "forbid"}


class WriteRangeArgs(BaseModel):
    sheet: str = Field(description="Name of the worksheet to write to")
    start_cell: str = Field(
        description="Top-left cell to start writing at, in A1 notation, for example D2"
    )
    values: List[List[object]] = Field(
        description=(
            "2D array of values, row-major. Each inner list is one row. "
            "Use strings, numbers, booleans or null."
        )
    )

    model_config = {"extra": "forbid"}


class WriteFormulaArgs(BaseModel):
    sheet: str = Field(description="Name of the worksheet to write to")
    target_range: str = Field(
        description="Target cell or range in A1 notation, for example D2 or D2:D100"
    )
    formula: str = Field(
        description=(
            "Excel formula to write, starting with '='. When a range is given, the "
            "formula is written to every cell with relative references adjusted "
            "per row/column, exactly like filling down in Excel. Example: '=(B2-C2)/B2'"
        )
    )

    model_config = {"extra": "forbid"}


class CreateSheetArgs(BaseModel):
    sheet_name: str = Field(description="Name of the new worksheet to create")

    model_config = {"extra": "forbid"}


class SaveWorkbookArgs(BaseModel):
    """save_workbook takes no arguments."""

    model_config = {"extra": "forbid"}
