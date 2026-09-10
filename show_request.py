"""Print the exact messages + tool schemas the agent would send to the model
on the first step, for a given instruction. Does not call the API.

Usage:
    python show_request.py "Add a profit margin column to the Sales sheet"
"""

import json
import sys

from prompts import SYSTEM_PROMPT
from tools import get_tool_schemas


def main(argv: list[str]) -> int:
    prompt = argv[0] if argv else "Add a profit margin column to the Sales sheet."
    payload = {
        "model": "<OPENAI_MODEL>",
        "tool_choice": "auto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "tools": get_tool_schemas(),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
