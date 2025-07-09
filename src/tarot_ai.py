import openai, re, textwrap
from dataclasses import dataclass
from typing import List
from llm import LLM

from config import (
    INITIAL_SYSTEM_MSG,
    REINFORCEMENT_SYSTEM_MSG,
    CARDS_REINFORCEMENT_SYSTEM_MSG,
)

# ---------- moderation -------------------------------------
class FlaggedInputError(RuntimeError): pass


# ---------- command extraction -----------------------------
@dataclass
class AiCommands:
    questions_to_ask: List[str]
    draw_cards: int
    cleaned_content: str

CMD_QUESTION = re.compile(r"^QUESTION:\s+(.+)$", re.M)
CMD_DRAW     = re.compile(r"^PULL TAROT CARDS\s*:\s*(\d+)", re.M)

def extract_commands(text: str) -> AiCommands:
    questions = CMD_QUESTION.findall(text)
    draws     = [int(n) for n in CMD_DRAW.findall(text)]
    cleaned   = CMD_QUESTION.sub("", text)
    cleaned   = CMD_DRAW.sub("", cleaned)
    return AiCommands(questions, sum(draws), textwrap.dedent(cleaned).strip())

# ---------- chat completion --------------------------------
def get_ai_response(history: list[dict]) -> dict:
    """history already contains user/assistant turns; we prepend/append system msgs here."""
    messages = [{"role":"system", "content":INITIAL_SYSTEM_MSG}] + history

    last = history[-1]
    if last["role"]=="system" and last["content"].startswith("The selected cards were"):
        messages.append({"role":"system", "content":CARDS_REINFORCEMENT_SYSTEM_MSG})
    else:
        messages.append({"role":"system", "content":REINFORCEMENT_SYSTEM_MSG})

    llm = LLM()

    return llm.predict(messages)