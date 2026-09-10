"""Shared test fixtures. Living at the project root also puts the project
modules on ``sys.path`` for the test suite.
"""

import openpyxl
import pytest


@pytest.fixture
def workbook_path(tmp_path):
    """A small fixture workbook with a Sales sheet and a Notes sheet."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["Product", "Revenue", "Cost"])
    ws.append(["Widget", 100, 60])
    ws.append(["Gadget", 200, 150])
    ws.append(["Gizmo", 300, 90])
    wb.create_sheet("Notes")
    path = tmp_path / "example.xlsx"
    wb.save(path)
    return str(path)
