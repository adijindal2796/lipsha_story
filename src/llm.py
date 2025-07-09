from __future__ import annotations

"""llm.py – Unified LLM wrapper (Gemini‑first)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A minimal convenience layer that tries a Google **Gemini** model first and
falls back to **Cerebras** and then **DeepSeek** (OpenAI‑compatible) only when
necessary.

**Key design points (July 2025)**
---------------------------------
* **No baked‑in system prompt** – the caller is responsible for providing any
  `{"role": "system", "content": ...}` messages.
* The public API now mirrors the OpenAI chat format directly:

    ```python
    llm = LLM()
    answer = llm.predict([
        {"role": "system", "content": INITIAL_SYSTEM_MSG},
        {"role": "user", "content": "Hi there!"},
    ])
    ```

* Removed all history / template plumbing. Everything flows through the
  `messages` list.
"""

from typing import List, Dict, Any
import time

# ── 3rd‑party clients ──────────────────────────────────────────────────────
from openai import OpenAI
from google import genai
from google.api_core.exceptions import GoogleAPICallError
from google.genai import types  # type: ignore
from cerebras.cloud.sdk import Cerebras

# ── Project‑local settings & constants ─────────────────────────────────────
import config  # centralised literals & API keys

__all__ = ["LLM"]


class LLM:  # noqa: D101
    def __init__(
        self,
        *,
        deepseek_model: str | None = None,
        gemini_model: str | None = None,
    ) -> None:
        # ◉ Gemini (primary)
        self._gemini_client = genai.Client(api_key=config.GOOGLE_API_KEY)
        self._gemini_model = gemini_model or config.GEMINI_MODEL_ID

        # ◉ Cerebras (secondary)
        self._cerebras_client = Cerebras(
            api_key="csk-v5c884pp3x3ty8he5tvx2jw3hv2mrnhdmjw992dhy8382c6p"
        )
        self._cerebras_model = "llama-3.3-70b"

        # ◉ DeepSeek / OpenAI‑compatible (tertiary)
        self._openai_client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )
        self._deepseek_model = deepseek_model or config.OPENAI_MODEL_ID

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def predict(
        self,
        messages: List[Dict[str, str]],
        *,
        max_retries: int = 3,
        retry_delay: float = 8.0,
    ) -> str:
        """Chat completion with automatic provider fallback.

        Parameters
        ----------
        messages : list[dict]
            Standard OpenAI‑style message list (`role` ∈ {system,user,assistant}).
        """
        print("MESSAGES IN:", messages)

        # Helper: flatten messages → text prompt for Gemini (no native chat API)
        prompt = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)
        print("PROMPT\n", prompt)

        # ── 1 / Gemini ────────────────────────────────────────────────
        attempt = 0
        while attempt <= max_retries:
            try:
                gemini_resp = self._gemini_client.models.generate_content(
                    model=self._gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        safety_settings=[
                            types.SafetySetting(
                                category=cat,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            )
                            for cat in (
                                types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                            )
                        ],
                        temperature=1.0,
                        top_k=300,
                        top_p=1.0,
                    ),
                )
                text = getattr(gemini_resp, "text", None)
                if text and text.strip():
                    print("LLM Ans (Gemini):", text)
                    return text  # type: ignore[attr-defined]

                fb = getattr(gemini_resp, "prompt_feedback", None)
                print("[LLM] Gemini empty response; block reason:", getattr(fb, "block_reason", "n/a"))
                raise GoogleAPICallError("Gemini produced no candidates")

            except GoogleAPICallError as err:
                attempt += 1
                if attempt > max_retries:
                    print("[LLM] Gemini error – falling back to Cerebras:", err)
                    break
                time.sleep(retry_delay * attempt)
            except Exception as err:  # pylint: disable=broad-except
                print("[LLM] Unexpected Gemini error – falling back to Cerebras:", err)
                break

        # ── 2 / Cerebras ──────────────────────────────────────────────
        attempt = 0
        while attempt <= max_retries:
            try:
                cb_resp = self._cerebras_client.chat.completions.create(
                    messages=messages,
                    model=self._cerebras_model,
                    max_completion_tokens=2048,
                    temperature=0.2,
                    top_p=1.0,
                    stream=False,
                )
                ans = cb_resp.choices[0].message.content.strip()
                print("LLM Ans (Cerebras):", ans)
                return ans

            except Exception as cb_err:  # pylint: disable=broad-except
                attempt += 1
                if attempt > max_retries:
                    print("[LLM] Cerebras error – falling back to DeepSeek:", cb_err)
                    break
                time.sleep(retry_delay * attempt)

        # ── 3 / DeepSeek (OpenAI‑compatible) ──────────────────────────
        attempt = 0
        while True:
            try:
                completion = self._openai_client.chat.completions.create(
                    model=self._deepseek_model,
                    max_tokens=4000,
                    temperature=0.6,
                    top_p=1.0,
                    messages=messages,
                )
                ans = completion.choices[0].message.content.strip()
                print("LLM Ans (DeepSeek):", ans)
                return ans

            except Exception as ds_err:  # pylint: disable=broad-except
                attempt += 1
                if attempt >= max_retries:
                    raise RuntimeError(
                        f"DeepSeek failed after {max_retries} retries"
                    ) from ds_err
                time.sleep(retry_delay * attempt)



if __name__ == "__main__":
    """Run a simple smoke test when executed directly.

    Example usage: `python llm.py "What’s the weather in Bengaluru?"`
    """
    import sys

    user_question = " ".join(sys.argv[1:]) or "Tell me a short story set in Bengaluru."

    # Fallback to a generic system prompt if none is defined in config
    INITIAL_SYSTEM_MSG: str = getattr(config, "INITIAL_SYSTEM_MSG", "You are a helpful assistant.")

    chat_messages = [
        {"role": "system", "content": INITIAL_SYSTEM_MSG},
        {"role": "user", "content": user_question},
    ]

    llm = LLM()
    reply = llm.predict(chat_messages)

    print("\n--- Model response ---\n")
    print(reply)
