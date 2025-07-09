# app.py  (excerpt – put this below your imports and helper functions)

import random, uuid
import streamlit as st
from config        import TAROT_DECK                     # deck list + paths
from ui            import header, intro_view             # banner + pre-chat UI
from tarot_ai      import (
    extract_commands,
    get_ai_response,
    FlaggedInputError,
)
from session_mgr   import (
    ChatSession,
    load_session,
    new_session,
    save_session,
)

# ────────────────────────────────────────────────────────────────
def main():
    # ══════════ 1. bootstrap / resume session ═══════════════════
    qs_id = st.query_params.get("s", [None])[0]

    if "session_id" not in st.session_state:
        if qs_id and (chat := load_session(qs_id)):
            # ─ existing session ─
            st.session_state.update(
                dict(session_id=qs_id, chat_session=chat, started_chat=True)
            )
        else:
            # ─ brand-new session ─
            sid, chat, extra = new_session()
            st.session_state.update(extra)
            st.session_state.chat_session = chat

    chat: ChatSession = st.session_state.chat_session  # typed alias

    # ══════════ 2. page chrome + banner ═════════════════════════
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="collapsed",
        page_title="Aditya Tarot - Virtual Tarot Readings",
    )
    header(st.session_state.header_images)

    # ══════════ 3. pre-chat landing view ════════════════════════
    if not st.session_state.started_chat:
        intro_view()
        return  # nothing else to do yet

    # ══════════ 4. reading UI – top avatar & history ════════════
    st.image(st.session_state.Aditya_image, width=180)

    for msg in chat.history:
        if msg["role"] == "assistant":
            st.write(extract_commands(msg["content"]).cleaned_content)
        elif msg["role"] == "user":
            st.markdown(
                f"<div style='color: yellow;'>&gt; {msg['content']}</div>",
                unsafe_allow_html=True,
            )
        elif msg["role"] == "system" and msg["content"].startswith(
            "The selected cards were"
        ):
            st.markdown(
                f"<div style='color: red;'>&gt; {msg['content']}</div>",
                unsafe_allow_html=True,
            )

    ai_cmds = extract_commands(chat.history[-1]["content"])

    # ══════════ 5. finished reading → closing screen ════════════
    if not (ai_cmds.draw_cards or ai_cmds.questions_to_ask):
        st.image(st.session_state.closing_image)
        st.subheader(f"[Link to this session](?s={st.session_state.session_id})")
        if st.button("Return Home", use_container_width=True):
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()
        return

    # ══════════ 6. interactive form (Q&A + card pulls) ═════════
    virtual_cards = st.session_state.card_draw_type == "Draw cards virtually"
    with st.form("user-input-form"):
        # --- answer text boxes ----------------------------------
        answers = [st.text_area(q) for q in ai_cmds.questions_to_ask]

        # --- card-drawing widgets -------------------------------
        drawn_cards = []
        n = ai_cmds.draw_cards
        if n:
            st.write(f"Pull {n} card{'s' if n > 1 else ''}")

            if virtual_cards:  # ★ virtual deck
                cols = st.columns((1, 1, 1, 2))
                seed = cols[0].text_input(
                    "Shuffle Value",
                    value=st.session_state.get("shuffle_seed", uuid.uuid4().hex),
                    help="Seed for virtual shuffle",
                )
                st.session_state.shuffle_seed = seed

                if cols[1].form_submit_button("Shuffle"):
                    st.session_state.shuffle_seed = uuid.uuid4().hex
                    st.rerun()

                if cols[2].form_submit_button("Pull Card"):
                    if len(st.session_state.chosen_virtual_cards) == n:
                        st.error("Already pulled requested number of cards")
                    else:
                        rng = random.Random(seed)
                        pool = [
                            c
                            for c in TAROT_DECK
                            if c
                            not in st.session_state.chosen_virtual_cards
                            + st.session_state.all_chosen_cards
                        ]
                        st.session_state.chosen_virtual_cards.append(rng.choice(pool))
                        st.rerun()

                # freeze UI display for pulled cards
                for i in range(n):
                    val = (
                        st.session_state.chosen_virtual_cards[i]
                        if i < len(st.session_state.chosen_virtual_cards)
                        else ""
                    )
                    drawn_cards.append(st.text_input(f"Card {i+1}", value=val, disabled=True))

            else:  # ★ physical deck
                if st.form_submit_button("Switch to drawing virtual cards"):
                    st.session_state.card_draw_type = "Draw cards virtually"
                    st.session_state.chosen_virtual_cards = []
                    st.rerun()

                deck = [""] + TAROT_DECK
                for i in range(n):
                    default = (
                        st.session_state.chosen_virtual_cards[i]
                        if i < len(st.session_state.chosen_virtual_cards)
                        else ""
                    )
                    idx = deck.index(default) if default else 0
                    drawn_cards.append(
                        st.selectbox(f"Card {i+1}", deck, index=idx, key=f"card-{i}")
                    )

        # --- SUBMIT handler -------------------------------------
        if st.form_submit_button("Submit"):
            # validation
            if len([a for a in answers if a]) != len(ai_cmds.questions_to_ask) or (
                n and len([c for c in drawn_cards if c]) != n
            ):
                st.error("Answer all questions and draw all cards before submitting")
                st.stop()
            if len(set(drawn_cards)) != len(drawn_cards):
                st.error("Cannot choose the same card more than once")
                st.stop()

            # append user answers
            try:
                if answers:
                    combined = "\n\n".join(answers)
                    chat.user_says(combined)

                # append selected cards
                if drawn_cards:
                    chat.system_says("The selected cards were: " + ", ".join(drawn_cards))
                    st.session_state.all_chosen_cards.extend(drawn_cards)
                    st.session_state.chosen_virtual_cards = []

                # call the LLM (with simple retry loop)
                with st.spinner("Generating AI response"):
                    for attempt in range(3):
                        resp = get_ai_response(chat.history)
                        print("debug here")
                        print(resp)
                        try:
                            extract_commands(resp)
                            break  # good response!
                        except Exception:
                            if attempt == 2:
                                st.error("Error generating your reading, please retry")
                                st.stop()

                chat.assistant_says(resp)


            except FlaggedInputError:
                st.session_state.flagged_input = True
                save_session(st.session_state.session_id, chat, st.session_state)
                st.rerun()

            # persist & refresh
            save_session(st.session_state.session_id, chat, st.session_state)
            st.rerun()

    # ══════════ 7. autosave after any UI render ════════════════
    save_session(st.session_state.session_id, chat, st.session_state)


if __name__ == "__main__":
    main()