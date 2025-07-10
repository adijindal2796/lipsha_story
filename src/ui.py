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
def header(img_paths):
    """Three images side-by-side beneath a title."""
    _inject_css()
    with st.container():
        st.markdown(
            "<h1 style='text-align:center;margin-top:-0.5rem; "
            "color:var(--accent);letter-spacing:0.02em;'>Aditya Tarot</h1>",
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 1, 1])
        for col, img in zip(cols, img_paths):
            with col:
                st.markdown('<div class="tarot-banner">', unsafe_allow_html=True)
                st.image(img)
                st.markdown("</div>", unsafe_allow_html=True)


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