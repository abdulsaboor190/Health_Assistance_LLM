"""
app.py — Aegis Health AI: Navigation Host
==========================================
Entry point for the multi-page app.
  • Sets page config (must be first Streamlit call)
  • Initialises all shared session state
  • Injects shared CSS via theme.py
  • Renders the shared sidebar (logo, toggle, role, metrics, reset)
  • Hands off to the active page via st.navigation
"""

import streamlit as st
from theme import get_tokens, inject_css, inject_sidebar_js

# ──────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG (must be the very first Streamlit call)
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aegis Health AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────
# 2. SHARED SESSION STATE
# ──────────────────────────────────────────────────────────────────
for _k, _v in {
    "theme":               "day",
    "messages":            [],
    "chat_history_tuples": [],
    "current_role":        "patient",
    "num_chunks":          3,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ──────────────────────────────────────────────────────────────────
# 3. DESIGN TOKENS + CSS
# ──────────────────────────────────────────────────────────────────
D  = get_tokens()     # all colours / fonts for the current theme
inject_css(D)         # injects the master CSS block

# Extract a few local variables for use in sidebar HTML
_acc    = D["acc"]
_tx     = D["tx"]
_mute   = D["mute"]
_surf2  = D["surf2"]
_bd     = D["bd"]
_bda    = D["bd_a"]
_green  = D["green"]
_gr_bg  = D["gr_bg"]
_fb     = D["fb"]
_mt2    = D["mute2"]

# ──────────────────────────────────────────────────────────────────
# 4. MULTI-PAGE NAVIGATION DEFINITION
# ──────────────────────────────────────────────────────────────────
chat_page = st.Page(
    "pages/chat_assistant.py",
    title="Chat Assistant",
    icon="💬",
)
symptom_page = st.Page(
    "pages/symptom_checker.py",
    title="Symptom Checker",
    icon="🩺",
)
kb_page = st.Page(
    "pages/knowledge_base.py",
    title="Knowledge Base",
    icon="📚",
)

pg = st.navigation([chat_page, symptom_page, kb_page])

# ──────────────────────────────────────────────────────────────────
# 5. SHARED SIDEBAR (shown on every page)
# ──────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Logo ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:6px;'>"
        f"  <div class='logo-icon'>✚</div>"
        f"  <div>"
        f"    <div style='font-size:1rem; font-weight:800; color:{_tx};'>Aegis Health AI</div>"
        f"    <div style='font-size:0.64rem; color:{_mute}; letter-spacing:0.05em;'>Gemini 2.5 Flash · RAG</div>"
        f"  </div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Theme Toggle ──────────────────────────────────────────────
    T        = st.session_state["theme"]
    tgl_ico  = "🌙" if T == "day" else "☀️"
    tgl_lbl  = "Night" if T == "day" else "Day"
    st.markdown("<div class='toggle-wrap' style='margin-top:10px;'>", unsafe_allow_html=True)
    if st.button(f"{tgl_ico}  {tgl_lbl} mode", key="sb_theme_toggle", use_container_width=True):
        st.session_state["theme"] = "night" if T == "day" else "day"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────
    # ── Consultation Mode — two real buttons that switch role instantly
    # The decorative HTML cards were replaced because they had no click
    # handler. Now we use st.button() so the switch is immediate.
    # ──────────────────────────────────────────────────────────────────
    st.markdown("<span class='slabel'>Consultation Mode</span>", unsafe_allow_html=True)

    is_p  = (st.session_state.current_role == "patient")

    # Active button gets accent background; inactive gets ghost style
    _p_style  = "role-active-btn" if is_p      else "role-idle-btn"
    _d_style  = "role-active-btn" if not is_p  else "role-idle-btn"

    # Inject per-render CSS for the two role button states
    st.markdown(f"""
<style>
/* Active role button */
div.role-active-btn .stButton > button {{
    background-color : {_acc}  !important;
    color            : #ffffff !important;
    border           : none    !important;
    font-weight      : 700     !important;
}}
/* Idle role button */
div.role-idle-btn .stButton > button {{
    background       : {_surf2} !important;
    color            : {_mute}  !important;
    border           : 1px solid {_bd} !important;
    font-weight      : 500     !important;
}}
div.role-idle-btn .stButton > button:hover {{
    border-color : {_acc} !important;
    color        : {_acc} !important;
    transform    : none   !important;
}}
</style>""", unsafe_allow_html=True)

    col_p, col_d = st.columns(2)
    with col_p:
        st.markdown(f"<div class='{_p_style}'>", unsafe_allow_html=True)
        if st.button("👤 Patient", key="btn_role_patient", use_container_width=True):
            st.session_state.current_role = "patient"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d:
        st.markdown(f"<div class='{_d_style}'>", unsafe_allow_html=True)
        if st.button("⚕️ Doctor", key="btn_role_doctor", use_container_width=True):
            st.session_state.current_role = "doctor"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    _role = st.session_state.current_role  # used by the rest of the app

    # Active role label (small confirmation text under buttons)
    _role_desc = "Plain-language explanations" if is_p else "Clinical terminology & depth"
    st.markdown(
        f"<div style='font-size:0.7rem; color:{_mute}; margin:6px 0 0 2px;'>"
        f"Mode: {_role_desc}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────
    # ── System Metrics — REAL values read from disk + FAISS index
    # ──────────────────────────────────────────────────────────────────
    from pathlib import Path as _Path

    _data_dir = _Path(__file__).parent / "data"
    _vs_dir   = _Path(__file__).parent / "vectorstore"

    # Count actual PDFs on disk
    _n_pdfs = len(list(_data_dir.rglob("*.pdf"))) if _data_dir.exists() else 0

    # Try to read real chunk count from FAISS index
    _n_chunks = 0
    try:
        import faiss as _faiss
        _idx = _faiss.read_index(str(_vs_dir / "index.faiss"))
        _n_chunks = int(_idx.ntotal)
    except Exception:
        _n_chunks = 0   # index not built yet

    # Current k value and a fixed "ready" indicator
    _k_val   = st.session_state.get("num_chunks", 3)
    _chunks_display = f"{_n_chunks // 1000:.1f}k" if _n_chunks >= 1000 else str(_n_chunks)
    _status_val  = "✓ Live" if _vs_dir.exists() else "✗ Build"
    _status_col  = _green  if _vs_dir.exists() else _bda

    st.markdown("<span class='slabel'>System Metrics</span>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='metric-grid'>"
        f"  <div class='mbox'><div class='mval'>{_n_pdfs}</div><div class='mlbl'>PDFs</div></div>"
        f"  <div class='mbox'><div class='mval'>{_chunks_display}</div><div class='mlbl'>Chunks</div></div>"
        f"  <div class='mbox'><div class='mval'>{_k_val}</div><div class='mlbl'>Depth (k)</div></div>"
        f"  <div class='mbox'><div class='mval' style='color:{_status_col};font-size:0.9rem;'>{_status_val}</div>"
        f"      <div class='mlbl'>Index</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # ── Context Depth Slider ──────────────────────────────────────
    st.markdown("<span class='slabel'>Context Depth (k)</span>", unsafe_allow_html=True)
    st.session_state["num_chunks"] = st.slider(
        "k", 1, 10, st.session_state["num_chunks"],
        label_visibility="collapsed", key="k_slider",
    )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────
    # ── Memory status + Reset conversation button
    # ──────────────────────────────────────────────────────────────────
    n_turns = len(st.session_state.chat_history_tuples)
    mem_ico = "🧠" if n_turns else "💭"
    mem_txt = f"{n_turns} turn(s) in memory" if n_turns else "Empty memory"
    st.markdown(
        f"<div style='font-size:0.72rem; color:{_mt2}; margin-bottom:10px;'>"
        f"{mem_ico}  {mem_txt}</div>",
        unsafe_allow_html=True,
    )

    # Reset button — uses ghost style; confirms via success message then reruns
    st.markdown("<div class='ghost-btn'>", unsafe_allow_html=True)
    if st.button("↺  Reset conversation", use_container_width=True, key="reset_btn"):
        st.session_state["messages"]            = []
        st.session_state["chat_history_tuples"] = []
        st.success("✓ Conversation cleared.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# 6. RUN THE ACTIVE PAGE
# ──────────────────────────────────────────────────────────────────
# Injects a floating '▶' button that appears whenever the sidebar is
# collapsed — JS approach is used because the native Streamlit expand
# button lives in a transparent header and may not be in the DOM.
# We call this BEFORE pg.run() to ensure the JS logic is active.
# ──────────────────────────────────────────────────────────────────
inject_sidebar_js(D)

pg.run()
