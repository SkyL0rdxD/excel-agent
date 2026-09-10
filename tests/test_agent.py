"""Agent loop: termination on a plain answer, recovery, and MAX_STEPS."""

import openpyxl
import pytest

import agent
from config import MAX_STEPS
from model import ModelResponse, ToolCall


def test_agent_returns_final_answer_when_no_tool_calls(monkeypatch, workbook_path):
    def fake_call_model(messages, tools):
        return ModelResponse(
            text="All done.",
            tool_calls=[],
            assistant_message={"role": "assistant", "content": "All done."},
        )

    monkeypatch.setattr(agent, "call_model", fake_call_model)
    assert agent.run_agent("say hi", workbook_path) == "All done."


def test_agent_executes_a_tool_then_finishes(monkeypatch, workbook_path):
    calls = {"n": 0}

    def fake_call_model(messages, tools):
        calls["n"] += 1
        if calls["n"] == 1:
            return ModelResponse(
                text=None,
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="write_formula",
                        arguments={
                            "sheet": "Sales",
                            "target_range": "D2:D4",
                            "formula": "=(B2-C2)/B2",
                        },
                    )
                ],
                assistant_message={
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "function": {
                                "name": "write_formula",
                                "arguments": "{}",
                            },
                        }
                    ],
                },
            )
        # Second turn: the tool result is in the conversation.
        last = messages[-1]
        assert last["role"] == "tool"
        assert '"success": true' in last["content"]
        return ModelResponse(
            text="Added margin column D.",
            tool_calls=[],
            assistant_message={"role": "assistant", "content": "Added margin column D."},
        )

    monkeypatch.setattr(agent, "call_model", fake_call_model)
    out = agent.run_agent("add margin", workbook_path)
    assert out == "Added margin column D."
    wb = openpyxl.load_workbook(workbook_path)
    assert wb["Sales"]["D3"].value == "=(B3-C3)/B3"


def test_agent_raises_after_max_steps(monkeypatch, workbook_path):
    def fake_call_model(messages, tools):
        return ModelResponse(
            text=None,
            tool_calls=[ToolCall(id="c", name="inspect_workbook", arguments={})],
            assistant_message={
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "c",
                        "type": "function",
                        "function": {
                            "name": "inspect_workbook",
                            "arguments": "{}",
                        },
                    }
                ],
            },
        )

    monkeypatch.setattr(agent, "call_model", fake_call_model)
    with pytest.raises(agent.MaxStepsExceeded):
        agent.run_agent("loop", workbook_path)


def test_agent_feeds_tool_errors_back_to_model(monkeypatch, workbook_path):
    seen = {}

    def fake_call_model(messages, tools):
        if any(m.get("role") == "tool" for m in messages):
            seen["tool_content"] = messages[-1]["content"]
            return ModelResponse(
                text="Recovered.",
                tool_calls=[],
                assistant_message={"role": "assistant", "content": "Recovered."},
            )
        return ModelResponse(
            text=None,
            tool_calls=[
                ToolCall(
                    id="c1",
                    name="read_range",
                    arguments={"sheet": "DoesNotExist", "cell_range": "A1:B2"},
                )
            ],
            assistant_message={
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "read_range", "arguments": "{}"},
                    }
                ],
            },
        )

    monkeypatch.setattr(agent, "call_model", fake_call_model)
    out = agent.run_agent("read bad sheet", workbook_path)
    assert out == "Recovered."
    assert '"success": false' in seen["tool_content"]
    assert MAX_STEPS == 10
