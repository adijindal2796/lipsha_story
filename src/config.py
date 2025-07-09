from pathlib import Path
import os


# --- paths -------------------------------------------------
DEFAULT_SESSION_DIR = Path.home() / ".Aditya_tarot_sessions"
SESSION_DIR = Path(os.getenv("SESSION_DIR", DEFAULT_SESSION_DIR))
SESSION_DIR.mkdir(parents=True, exist_ok=True)

PACKAGE_ROOT = Path(__file__).parent
IMAGE_DIR     = PACKAGE_ROOT / "images"

# --- models / prompts --------------------------------------
from utils.tarot import TAROT_DECK                      # external helper
from utils.messages import (                            # prompt strings
    REINFORCEMENT_SYSTEM_MSG,
    INITIAL_SYSTEM_MSG,
    INTROS,
    CARDS_REINFORCEMENT_SYSTEM_MSG,
)

OPENAI_API_KEY    = "40ce380b-179e-4041-a7a7-a9e5227d799c"
OPENAI_BASE_URL   = "https://api.kluster.ai/v1"
OPENAI_MODEL_ID   = "deepseek-ai/DeepSeek-V3-0324"

GOOGLE_API_KEY    = "AIzaSyDI4S1y0H_j6KwSW0I3QMphgouVyZgiyVQ"
GEMINI_MODEL_ID   = "gemini-2.0-flash-thinking-exp-01-21"