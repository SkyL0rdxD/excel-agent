"""All OpenAI-specific logic lives here.

The rest of the agent works with the provider-neutral ``ModelResponse`` and
``ToolCall`` dataclasses returned by :func:`call_model`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from config import OPENAI_MODEL, REQUEST_TIMEOUT, require_api_key

DEBUG = bool(os.getenv("AGENT_DEBUG"))

_TRANSIENT_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=require_api_key(),
            timeout=REQUEST_TIMEOUT,
            max_retries=0,  # retries are handled explicitly in call_model
        )
    return _client


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Any  # parsed dict, or the raw string if the model emitted invalid JSON


@dataclass
class ModelResponse:
    text: Optional[str]
    tool_calls: List[ToolCall] = field(default_factory=list)
    # Raw assistant message dict, ready to append back into the conversation.
    assistant_message: Dict[str, Any] = field(default_factory=dict)


def _parse_arguments(raw: Optional[str]) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def call_model(
    messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
) -> ModelResponse:
    """Send the conversation + tool schemas to the model and normalise the reply.

    Retries once on transient API errors; all other errors propagate.
    """
    client = _get_client()

    last_exc: Optional[Exception] = None
    for attempt in range(2):
        try:
            if DEBUG:
                print(
                    f"[model] POST chat.completions model={OPENAI_MODEL} "
                    f"messages={len(messages)} tools={len(tools)} "
                    f"(attempt {attempt + 1}, timeout {REQUEST_TIMEOUT}s)",
                    file=sys.stderr,
                    flush=True,
                )
            _t0 = time.monotonic()
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            if DEBUG:
                print(
                    f"[model] <- response in {time.monotonic() - _t0:.1f}s",
                    file=sys.stderr,
                    flush=True,
                )
            break
        except _TRANSIENT_ERRORS as exc:
            last_exc = exc
            if attempt == 1:
                raise RuntimeError(
                    f"Model API failed after one retry: {exc}"
                ) from exc
    else:  # pragma: no cover - loop always breaks or raises
        raise RuntimeError(f"Model API failed: {last_exc}")

    message = completion.choices[0].message

    tool_calls: List[ToolCall] = []
    for tc in message.tool_calls or []:
        tool_calls.append(
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=_parse_arguments(tc.function.arguments),
            )
        )

    return ModelResponse(
        text=message.content,
        tool_calls=tool_calls,
        assistant_message=message.model_dump(exclude_none=True),
    )
