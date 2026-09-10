"""The autonomous agent loop: model call -> tool calls -> repeat."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from config import MAX_STEPS
from model import call_model
from prompts import SYSTEM_PROMPT
from tools import execute_tool, get_tool_schemas


DEBUG = bool(os.getenv("AGENT_DEBUG"))


def _debug(msg: str) -> None:
    if DEBUG:
        print(f"[agent] {msg}", file=sys.stderr, flush=True)


class MaxStepsExceeded(RuntimeError):
    """Raised when the agent does not finish within MAX_STEPS iterations."""


def run_agent(prompt: str, workbook_path: str) -> str:
    """Run the agent on a single natural-language instruction.

    Returns the model's concise final message. Tool errors are fed back to the
    model as structured results so it can recover; only a genuine failure to
    converge within MAX_STEPS raises.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    tools = get_tool_schemas()

    for step in range(1, MAX_STEPS + 1):
        _debug(f"step {step}/{MAX_STEPS}: calling model...")
        response = call_model(messages, tools)
        messages.append(response.assistant_message)

        if not response.tool_calls:
            _debug(f"step {step}: no tool calls, returning final answer")
            return (response.text or "").strip() or "(no response from model)"

        for tool_call in response.tool_calls:
            _debug(f"step {step}: -> {tool_call.name}({tool_call.arguments})")
            result = execute_tool(tool_call, workbook_path)
            _debug(f"step {step}: <- {json.dumps(result, default=str)[:200]}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    raise MaxStepsExceeded(
        f"Agent did not complete the request within MAX_STEPS ({MAX_STEPS}) steps."
    )
