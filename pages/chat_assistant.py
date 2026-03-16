"""
pages/chat_assistant.py — Chat Assistant Page
==============================================
The main RAG-powered conversational interface.
This file is executed by app.py via st.navigation.
All theme CSS is already injected by app.py before this runs.
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Allow imports from the parent directory (chain.py, safety.py, theme.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

from chain import ask
from safety import check_emergency, check_unsafe_input
from theme import get_tokens

# ── Get current theme tokens (already injected by app.py, but needed for inline styles)
D    = get_tokens()
_acc = D["acc"];  _tx   = D["tx"];   _mute = D["mute"]
_bd  = D["bd"];   _surf = D["surf"]; _surf2 = D["surf2"]
_mt2 = D["mute2"]; _app = D["app_bg"]
_ubg = D["u_bg"]; _utx  = D["u_tx"]
_ebg = D["emg_bg"]; _ebd = D["emg_bd"]; _etx = D["emg_tx"]
_fb  = D["fb"];   _fh   = D["fh"]
_grn = D["green"]; _gr_bg = D["gr_bg"]
_bda = D["bd_a"]

# Read shared state
role       = st.session_state.get("current_role", "patient")
num_chunks = st.session_state.get("num_chunks", 3)

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def render_sources(sources: list):
    """Shows source document references in a collapsible expander."""
    if not sources:
        return
    with st.expander(f"📎  {len(sources)} source(s) — view evidence"):
        for doc in sources:
            fname   = os.path.basename(doc.metadata.get("source", "PDF"))
            pg_raw  = doc.metadata.get("page", 0)
            pg      = (pg_raw + 1) if isinstance(pg_raw, int) else pg_raw
            preview = doc.page_content.strip().replace("\n", " ")[:200]
            st.markdown(
                f"<div class='src-card'>"
                f"<span class='src-fname'>📄 {fname}</span>"
                f"<span class='src-page'>p.{pg}</span>"
                f"<div class='src-prev'>\"{preview}...\"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ─────────────────────────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────────────────────────
T        = st.session_state["theme"]
mode_lbl = "Patient mode" if role == "patient" else "Clinical mode"
tgl_ico  = "🌙" if T == "day" else "☀️"
tgl_lbl  = "Night" if T == "day" else "Day"

col_l, col_r = st.columns([6, 1])
with col_l:
    st.markdown(
        f"<div class='topbar'>"
        f"  <span class='tb-title'>Health Assistant</span>"
        f"  <span class='status-dot'>● Online</span>"
        f"  <span class='mode-chip'>{mode_lbl}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
with col_r:
    st.markdown("<div class='toggle-wrap'>", unsafe_allow_html=True)
    if st.button(f"{tgl_ico} {tgl_lbl}", key="chat_theme_btn"):
        st.session_state["theme"] = "night" if T == "day" else "day"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# HERO (only shown when no messages yet)
# ─────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    if T == "day":
        _h1 = "Evidence-based medical<br>guidance at your fingertips"
    else:
        _h1 = "Precision <span style='color:" + _acc + ";'>medical</span> grounding"

    st.markdown(
        f"<div class='hero-tag'>Intelligent RAG Assistant</div>"
        f"<h1>{_h1}</h1>"
        f"<p style='color:{_mute}; font-size:1.05rem; max-width:580px; line-height:1.65; margin:12px 0 28px;'>"
        f"Every answer is cross-referenced against your curated PDF library. "
        f"Gemini 2.5 Flash retrieves and synthesizes medical evidence before responding."
        f"</p>",
        unsafe_allow_html=True,
    )

    # Quick starter pills
    _starters = ["Diabetes treatment", "Cardiac first aid", "Pharmacokinetics", "WHO standards"]
    pills_html = "".join(
        f"<span style='font-size:0.8rem; color:{_tx}; background:{_surf}; border:1px solid {_bd};"
        f"padding:8px 16px; border-radius:8px; cursor:pointer;'>{q} ↗</span>"
        for q in _starters
    )
    st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:8px; margin-bottom:40px;'>{pills_html}</div>",
                unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='user-row'><div class='user-bubble'>{msg['content']}</div></div>"
            f"<div class='user-meta'>You · just now</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant", avatar="🏥"):
            st.markdown(msg["content"])
            n = msg.get("source_count", 0)
            if n:
                st.markdown(
                    f"<div class='conf'>Aegis · Based on {n} source(s) · confidence: high</div>",
                    unsafe_allow_html=True,
                )
            if msg.get("sources"):
                render_sources(msg["sources"])

# ─────────────────────────────────────────────────────────────────
# CHAT INPUT + PROCESSING
# ─────────────────────────────────────────────────────────────────
query = st.chat_input("Enter clinical or health query…")

if query:
    st.session_state.messages.append(
        {"role": "user", "content": query, "sources": [], "source_count": 0}
    )
    st.rerun()

if (st.session_state.messages and
        st.session_state.messages[-1]["role"] == "user"):
    last_q = st.session_state.messages[-1]["content"]

    # Emergency check (shows banner but does not block the answer)
    if check_emergency(last_q):
        st.markdown(
            "<div class='emg-box'>🚨 <strong>CRITICAL: Emergency symptoms detected.</strong><br>"
            "Call <strong>115</strong> (Pakistan Rescue) · <strong>1122</strong> (Punjab) · "
            "<strong>911</strong> (International) immediately.</div>",
            unsafe_allow_html=True,
        )

    if check_unsafe_input(last_q):
        _ref = ("This request falls outside safe operational parameters. "
                "Please consult a qualified medical professional directly.")
        st.warning(f"⚠️  {_ref}")
        st.session_state.messages.append(
            {"role": "assistant", "content": _ref, "sources": [], "source_count": 0}
        )
    else:
        _mode_str = "Clinical" if role == "doctor" else "Patient-Friendly"
        with st.spinner(f"Analysing library — generating {_mode_str} answer…"):
            try:
                result  = ask(last_q, role, num_chunks, st.session_state.chat_history_tuples)
                answer  = result["answer"]
                sources = result["sources"]
                st.session_state.chat_history_tuples.append((last_q, answer))
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer,
                     "sources": sources, "source_count": len(sources)}
                )
                st.rerun()
            except FileNotFoundError as e:
                st.error(f"⚠️  Vector store missing. {e}  Run `ingest.py` first.")
            except Exception as e:
                st.error(f"❌  Unexpected error: {e}")

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='app-footer'>AI may produce errors. Always cross-reference "
    "with authorised medical literature. Not a substitute for professional advice.</div>",
    unsafe_allow_html=True,
)
