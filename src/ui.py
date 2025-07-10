import streamlit as st, html
from pathlib import Path
from config import IMAGE_DIR
from tarot_ai import extract_commands


# ─────────────────────────────────────────────
# global CSS – inject once
def _inject_css():
    if st.session_state.get("_custom_css"):  # only once per session
        return

    st.markdown(
        """
        <style>
            :root {
              --accent: #7e4cff;
              --user-bg: #fff7c9;
              --assistant-bg: #ede9ff;
              --system-bg: #ffe8e8;
            }
            /* parchment backdrop */
            body {
              background: radial-gradient(circle at 50% 0%, #fdf9f1 0%, #f7f3e8 85%);
              font-family: "Inter", "Segoe UI", sans-serif;
            }
            /* banner overlay */
            .tarot-banner img {
              filter: brightness(0.9);
              border-radius: 12px;
            }
            /* tweak default chat bubble paddings */
            .stChatMessage { padding-bottom: 0.4rem; }
        </style>

        <!-- load Inter font -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
              rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
    st.session_state._custom_css = True


# ─────────────────────────────────────────────
import streamlit as st
from pathlib import Path
from typing import Sequence, Union

ImagePath = Union[str, Path]

def header(
    img_paths: Sequence[ImagePath],
    title: str = "Aditya Tarot’s Reading",
) -> None:
    """Render a responsive, three-panel banner with a stylized title.

    Parameters
    ----------
    img_paths : Sequence[str | Path]
        Paths or URLs of up to three images to show side-by-side.
    title : str
        Display title (defaults to “Aditya Tarot’s Reading”).
    """
    _inject_css()  # inject only once per session

    # Title
    st.markdown(f"<h1 class='tarot-title'>{title}</h1>", unsafe_allow_html=True)

    # Three evenly-spaced columns with a little breathing room
    cols = st.columns(3, gap="small")
    for col, img in zip(cols, img_paths[:3]):          # ignore extras gracefully
        with col:
            st.markdown('<div class="tarot-banner">', unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
def _inject_css() -> None:
    """Inject custom CSS once per session."""
    if st.session_state.get("_tarot_css_injected"):
        return
    st.session_state["_tarot_css_injected"] = True

    st.markdown(
        """
        <style>
        /* Google font for a touch of elegance */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');

        .tarot-title {
            font-family: 'Playfair Display', serif;
            text-align: center;
            margin: -0.3rem 0 1.2rem;
            letter-spacing: 0.03em;
            /* Fallback to Streamlit’s accent color var */
            color: var(--accent, #8e44ad);
            animation: fadeInDown 0.8s ease-out;
        }

        .tarot-banner img {
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,.25);
            transition: transform .35s ease, box-shadow .35s ease;
        }
        .tarot-banner img:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 6px 18px rgba(0,0,0,.35);
        }

        /* Mobile tweaks */
        @media (max-width: 768px) {
            .tarot-banner img { margin-bottom: 0.8rem; }
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
def intro_view():
    _inject_css()
    st.markdown(
        "<h2 style='text-align:center;margin-top:2rem;'>Shall we begin?</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;'>Draw cards virtually and let the symbols speak.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Begin Reading 🔮", use_container_width=True):
        st.session_state.card_draw_type = "Draw cards virtually"
        st.session_state.started_chat = True


# ─────────────────────────────────────────────
def _avatar(role: str):
    if role == "user":
        return "🧑"
    if role == "assistant":
        return "🧙"
    return "🔮"


def render_chat(history):
    _inject_css()
    for msg in history:
        role = msg["role"]
        if role == "assistant":
            content = extract_commands(msg["content"]).cleaned_content
        elif role == "user":
            content = msg["content"]
        elif role == "system" and msg["content"].startswith("The selected cards were"):
            role, content = "system", msg["content"]
        else:
            continue

        with st.chat_message(role, avatar=_avatar(role)):
            # Use Markdown so we keep bold/italics, preserve newlines
            st.markdown(html.escape(content).replace("\n", "  \n"))