import random, uuid
import streamlit as st
from config import IMAGE_DIR, TAROT_DECK
from tarot_ai import extract_commands
from session_mgr import ChatSession

# ---------- one-liners that emit Streamlit elements --------
def header(images):          # 3-wide banner
    _, c1, c2, c3, _ = st.columns(5)
    for c,img in zip((c1,c2,c3), images): c.image(img)

def intro_view():
    st.markdown("<h1 style='text-align: center; color: purple;'>Shall we begin?</h1>", unsafe_allow_html=True)
    draw_type = st.selectbox("How would you like to select cards?",
                             ["Draw cards virtually", "Draw cards from your own tarot deck"])
    if st.button("Yes", use_container_width=True):
        st.session_state.card_draw_type = draw_type
        st.session_state.started_chat   = True

# ... add other small helpers: chat_history_view(), card_inputs_form(), closing_view(), etc.