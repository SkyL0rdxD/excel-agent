"""Central configuration loaded from the environment / .env file."""

import os

from dotenv import load_dotenv

load_dotenv()

# LLM provider configuration.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Agent loop configuration.
MAX_STEPS = 10

# Per-request timeout (seconds) for model API calls, so a network stall fails
# fast instead of hanging forever.
REQUEST_TIMEOUT = 30.0

# Number of preview rows returned by inspect_workbook per sheet.
INSPECT_PREVIEW_ROWS = 5


def require_api_key() -> str:
    """Return the configured API key or raise a clear error."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return OPENAI_API_KEY
