# Excel Agent

An autonomous Excel editing agent built in Python.

The agent uses an LLM with structured tool calls to inspect and modify
Excel workbooks through OpenPyXL.

## Architecture

User instruction
→ Agent loop
→ LLM
→ Tool call
→ Pydantic validation
→ OpenPyXL
→ Excel workbook
→ Tool result
→ LLM

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt