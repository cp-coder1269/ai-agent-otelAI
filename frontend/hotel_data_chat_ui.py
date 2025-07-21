"""hotel_data_chat_ui.py
Streamlit front‑end for the Hotel Data Chat API.
Two‑pane layout (sidebar + main chat) with dark‑mode toggle, rich‑content
rendering, and real‑time chunk streaming of AI responses.

Key fixes (2025‑07‑19)
---------------------
* **Dark‑mode:** broader CSS selectors so *all* elements switch colours.
* **Clear chat / theme toggle:** replaced deprecated `st.experimental_rerun()`
  with `st.rerun()` (Streamlit ≥ 1.30). Falls back gracefully for older
  versions.
* Retains rich‑block parsing (markdown / table / code) and traceability meta.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Helper – render rich‑content blocks
# ─────────────────────────────────────────────────────────────────────────────

def _render_traceability(meta: Dict[str, Any]) -> None:
    """Display file / sheet / columns metadata when provided by backend."""
    file = meta.get("file_name")
    sheet = meta.get("sheet_name")
    cols = meta.get("columns")
    if not any([file, sheet, cols]):
        return

    bullet_lines: List[str] = []
    if file:
        bullet_lines.append(f"**File:** {file}")
    if sheet:
        bullet_lines.append(f"**Sheet:** {sheet}")
    if cols:
        if isinstance(cols, (list, tuple)):
            cols = ", ".join(map(str, cols))
        bullet_lines.append(f"**Columns:** {cols}")

    st.markdown("\n".join(bullet_lines))


def _render_blocks(blocks_payload: Any) -> None:
    """Render backend response blocks according to their declared type."""
    if isinstance(blocks_payload, dict):
        _render_traceability(blocks_payload)
        blocks = blocks_payload.get("blocks", [])
    else:
        blocks = blocks_payload

    for block in blocks:
        btype = block.get("type")
        if btype == "markdown":
            st.markdown(block.get("content", ""), unsafe_allow_html=True)
        elif btype == "table":
            cols = block.get("columns", [])
            data = block.get("data", [])
            df = pd.DataFrame(data, columns=cols)
            st.dataframe(df, use_container_width=True)
        elif btype == "code":
            st.code(block.get("content", ""), language=block.get("language", ""))
        else:
            st.warning(f"Unknown block type: {btype}")

# ─────────────────────────────────────────────────────────────────────────────
# Page / session state
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Hotel Data Chat", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = [  # type: ignore
        {"role": "ai", "content": "Ask me anything about your hotel data \U0001F4C8"}
    ]

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "api_base" not in st.session_state:
    st.session_state.api_base = "https://ai-agent-otelai.onrender.com"

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar – settings & controls
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    api_base = st.text_input(
        label="Backend URL",
        value=st.session_state.api_base,
        help="Base URL where the FastAPI service is running (e.g. http://localhost:8000)",
    )
    st.session_state.api_base = api_base.strip().rstrip("/")

    # Dark‑mode toggle
    if st.toggle("🌗 Dark mode", value=st.session_state.dark_mode, key="dm_tog"):
        st.session_state.dark_mode = True
    else:
        st.session_state.dark_mode = False

    if st.button("🗑️ Clear chat", help="Remove previous conversation history"):
        st.session_state.messages = [
            {"role": "ai", "content": "Chat cleared. Ask me anything!"}
        ]
        # Rerun the script to refresh UI
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Dark‑mode CSS (applied on every rerun)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        /* Backgrounds */
        html, body, [data-testid="stAppViewContainer"], section.main {
            background-color: #0e1117 !important;
            color: #c9d1d9 !important;
        }
        /* Chat bubbles & markdown */
        .stChatMessage, .stMarkdown, .stCodeBlock, pre, code {
            color: #c9d1d9 !important;
            background-color: #161b22 !important;
        }
        /* Text inputs */
        input, textarea {
            background-color: #161b22 !important;
            color: #c9d1d9 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Chat display area
# ─────────────────────────────────────────────────────────────────────────────
chat_container = st.container()

# Render history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        chat_container.chat_message("user").markdown(msg["content"])
    else:
        try:
            parsed = json.loads(msg["content"])
            with chat_container.chat_message("assistant"):
                _render_blocks(parsed)
        except (json.JSONDecodeError, TypeError):
            chat_container.chat_message("assistant").markdown(msg["content"], unsafe_allow_html=False)

# ─────────────────────────────────────────────────────────────────────────────
# Backend streaming helper
# ─────────────────────────────────────────────────────────────────────────────

def _stream_chat(history: List[Dict[str, str]]):
    url = f"{st.session_state.api_base}/api/v1/chat"
    payload = {"messages": history}
    with requests.post(url, json=payload, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_lines(decode_unicode=True):
            if chunk:
                yield chunk

# ─────────────────────────────────────────────────────────────────────────────
# Input area
# ─────────────────────────────────────────────────────────────────────────────
if user_text := st.chat_input("Type your question and press Enter"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    chat_container.chat_message("user").markdown(user_text)

    # Assistant placeholder
    with chat_container.chat_message("assistant"):
        placeholder = st.empty()
        chunks: List[str] = []
        for token in _stream_chat(st.session_state.messages):
            chunks.append(token)
            placeholder.markdown("".join(chunks))

        full = "".join(chunks).strip()
        placeholder.empty()
        try:
            _render_blocks(json.loads(full))
        except json.JSONDecodeError:
            st.markdown(full, unsafe_allow_html=False)

        # Store raw backend reply
        st.session_state.messages.append({"role": "ai", "content": full})
