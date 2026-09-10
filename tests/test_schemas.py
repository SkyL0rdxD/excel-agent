"""Validation behaviour of the Pydantic tool-argument models."""

import pytest
from pydantic import ValidationError

from schemas import (
    CreateSheetArgs,
    ReadRangeArgs,
    WriteFormulaArgs,
    WriteRangeArgs,
)


def test_valid_read_range_args():
    args = ReadRangeArgs(sheet="Sales", cell_range="A1:C10")
    assert args.sheet == "Sales"
    assert args.cell_range == "A1:C10"


def test_read_range_args_missing_field():
    with pytest.raises(ValidationError):
        ReadRangeArgs(sheet="Sales")


def test_read_range_args_reject_extra_field():
    with pytest.raises(ValidationError):
        ReadRangeArgs(sheet="Sales", cell_range="A1", bogus=1)


def test_valid_write_range_args():
    args = WriteRangeArgs(
        sheet="Sales", start_cell="D2", values=[[1, 2], [3, 4]]
    )
    assert args.values == [[1, 2], [3, 4]]


def test_write_range_args_reject_non_2d_values():
    with pytest.raises(ValidationError):
        WriteRangeArgs(sheet="Sales", start_cell="D2", values="nope")


def test_valid_write_formula_args():
    args = WriteFormulaArgs(
        sheet="Sales", target_range="D2:D4", formula="=(B2-C2)/B2"
    )
    assert args.formula.startswith("=")


def test_create_sheet_args_requires_name():
    with pytest.raises(ValidationError):
        CreateSheetArgs()
