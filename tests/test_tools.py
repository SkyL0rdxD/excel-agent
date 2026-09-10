"""Tool registry: schema generation, dispatch and structured error handling."""

from types import SimpleNamespace

from tools import execute_tool, get_tool_schemas

EXPECTED_TOOLS = {
    "inspect_workbook",
    "read_range",
    "write_range",
    "write_formula",
    "create_sheet",
    "save_workbook",
}


def _call(name, arguments):
    return SimpleNamespace(id="call_1", name=name, arguments=arguments)


def test_get_tool_schemas_covers_all_tools():
    schemas = get_tool_schemas()
    names = {s["function"]["name"] for s in schemas}
    assert names == EXPECTED_TOOLS
    for schema in schemas:
        assert schema["type"] == "function"
        assert schema["function"]["parameters"]["type"] == "object"


def test_execute_tool_dispatches_to_function(workbook_path):
    result = execute_tool(
        _call("read_range", {"sheet": "Sales", "cell_range": "A1:C1"}),
        workbook_path,
    )
    assert result["success"] is True
    assert len(result["cells"]) == 3


def test_execute_tool_unknown_tool(workbook_path):
    result = execute_tool(_call("frobnicate", {}), workbook_path)
    assert result["success"] is False
    assert "Unknown tool" in result["error"]


def test_execute_tool_returns_validation_errors(workbook_path):
    result = execute_tool(_call("read_range", {"sheet": "Sales"}), workbook_path)
    assert result["success"] is False
    assert "validation_errors" in result


def test_execute_tool_wraps_missing_sheet_error(workbook_path):
    result = execute_tool(
        _call("read_range", {"sheet": "Ghost", "cell_range": "A1:B2"}),
        workbook_path,
    )
    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_execute_tool_non_dict_arguments(workbook_path):
    result = execute_tool(_call("read_range", "A1:C1"), workbook_path)
    assert result["success"] is False
    assert "JSON object" in result["error"]


def test_execute_tool_write_formula_roundtrip(workbook_path):
    result = execute_tool(
        _call(
            "write_formula",
            {"sheet": "Sales", "target_range": "D2:D4", "formula": "=(B2-C2)/B2"},
        ),
        workbook_path,
    )
    assert result["success"] is True
    assert result["cells_modified"] == 3
