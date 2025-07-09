import json, random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from utils.helpers import date_id
from config import SESSION_DIR, TAROT_DECK, IMAGE_DIR, INTROS
import json, inspect
from typing import Any, Mapping


def _jsonable(val: Any) -> bool:
    try:
        json.dumps(val)
        return True
    except (TypeError, OverflowError):
        return False

@dataclass
class ChatSession:
    history: list = field(default_factory=list)

    # convenience wrappers
    def user_says(self, msg):       self.history.append({"role": "user", "content": msg})
    def assistant_says(self, msg):  self.history.append({"role": "assistant", "content": msg})
    def system_says(self, msg):     self.history.append({"role": "system", "content": msg})

# ---------- persistence helpers ----------------------------
def _session_path(sid: str) -> Path:
    return SESSION_DIR / f"{sid}.json"

def load_session(sid: str) -> ChatSession | None:
    try:
        data = json.loads(_session_path(sid).read_text())
        return ChatSession(history=data["chat_history"])
    except Exception:
        return None

def save_session(sid: str,
                 chat_session: ChatSession,
                 extra_state: Mapping[str, Any]) -> None:
    """
    Persist chat history + any *simple* keys from Streamlit's session_state.
    Complex objects (functions, dataclasses, widgets, locks…) are skipped.
    """
    safe_state = {
        k: v
        for k, v in extra_state.items()
        if k != "chat_session" and _jsonable(v)
    }

    payload = {"chat_history": chat_session.history, **safe_state}

    _session_path(sid).write_text(json.dumps(payload, indent=2))

# ---------- first-time bootstrap ---------------------------
def new_session() -> tuple[str, ChatSession, dict]:
    sid = date_id()
    imgs = random.sample([p.as_posix() for p in (IMAGE_DIR).iterdir() if p.name!="Aditya.png"], k=4)

    cs = ChatSession()
    cs.assistant_says(random.choice(INTROS))

    state = dict(
        session_id=sid,
        reading_in_progress=True,
        started_chat=False,
        header_images=imgs[:3],
        Aditya_image=(IMAGE_DIR / "Aditya.png").as_posix(),
        closing_image=imgs[3],
        chosen_virtual_cards=[],
        all_chosen_cards=[],
        bad_responses=[],
        total_tokens_used=0,
    )
    return sid, cs, state