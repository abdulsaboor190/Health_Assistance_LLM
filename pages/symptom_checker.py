"""
pages/symptom_checker.py — Guided Symptom Checker
===================================================
A structured 3-step form that collects patient info, symptoms,
and severity, then uses the RAG chain to return a structured
clinical assessment.

Step 1 → Patient basics (age, sex, conditions)
Step 2 → Symptom selection (chip grid + free text)
Step 3 → Severity + duration → Analysis → Results card
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from chain import ask
from safety import check_emergency
from theme import get_tokens

# ─────────────────────────────────────────────────────────────────
# THEME TOKENS
# ─────────────────────────────────────────────────────────────────
D    = get_tokens()
_acc = D["acc"];   _tx  = D["tx"];   _mute = D["mute"]
_bd  = D["bd"];    _bda = D["bd_a"]; _surf = D["surf"]
_surf2 = D["surf2"]; _app = D["app_bg"]; _mt2 = D["mute2"]
_fb  = D["fb"];    _fh  = D["fh"];   _grn  = D["green"]
_ebg = D["emg_bg"]; _ebd = D["emg_bd"]; _etx = D["emg_tx"]
_wbg = D["warn_bg"]; _wbd = D["warn_bd"]; _wtx = D["warn_tx"]
_bntx = D["btn_tx"]

# ─────────────────────────────────────────────────────────────────
# SESSION STATE KEYS FOR THIS PAGE (prefix: sc_)
# ─────────────────────────────────────────────────────────────────
_SC_DEFAULTS = {
    "sc_step":          1,          # current step: 1, 2, or 3
    "sc_age":           30,
    "sc_sex":           "Not specified",
    "sc_conditions":    "",
    "sc_symptoms":      [],         # list of selected symptom strings
    "sc_other":         "",
    "sc_severity":      3,
    "sc_duration":      "1–3 days",
    "sc_result":        None,       # dict result from chain
    "sc_confirm_reset": False,
}
for _k, _v in _SC_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

SYMPTOM_LIST = [
    "Fever",           "Headache",          "Chest pain",
    "Fatigue",         "Nausea",            "Shortness of breath",
    "Dizziness",       "Back pain",         "Abdominal pain",
    "Blurred vision",  "Cough",             "Sore throat",
    "Joint pain",      "Skin rash",         "Swelling",
    "Palpitations",    "Loss of appetite",  "Vomiting",
]

DURATION_OPTIONS = [
    "Less than 24 hours",
    "1–3 days",
    "1 week",
    "More than 1 week",
]

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def _urgency_badge(label: str) -> str:
    """Returns an HTML badge for the urgency label."""
    cls_map = {
        "low":       "badge-low",
        "medium":    "badge-medium",
        "high":      "badge-high",
        "emergency": "badge-emergency",
    }
    cls = cls_map.get(label.lower(), "badge-medium")
    return f"<span class='badge {cls}'>{label.upper()}</span>"


def _step_bar(current: int):
    """Renders a 3-step progress bar at the top of the page."""
    steps = ["Patient Info", "Symptoms", "Severity & Analysis"]

    def _dot_cls(i):
        if i + 1 < current:  return "done"
        if i + 1 == current: return "active"
        return "idle"

    def _line_cls(i):
        return "done" if i + 1 < current else "idle"

    parts = []
    for i, label in enumerate(steps):
        parts.append(
            f"<div style='display:flex; flex-direction:column; align-items:center; gap:4px;'>"
            f"  <div class='step-dot {_dot_cls(i)}'>"
            f"    {'✓' if i + 1 < current else str(i + 1)}"
            f"  </div>"
            f"  <span style='font-size:0.62rem; color:{_mute}; white-space:nowrap;'>{label}</span>"
            f"</div>"
        )
        if i < len(steps) - 1:
            parts.append(f"<div class='step-line {_line_cls(i)}' style='margin-bottom:16px;'></div>")

    st.markdown(
        f"<div class='step-bar'>{''.join(parts)}</div>",
        unsafe_allow_html=True,
    )


def _build_query() -> str:
    """Builds a structured clinical query from all session state values."""
    syms = st.session_state.sc_symptoms
    if st.session_state.sc_other.strip():
        syms = syms + [st.session_state.sc_other.strip()]

    return (
        f"Clinical assessment request:\n"
        f"Patient: {st.session_state.sc_age} years old, "
        f"Sex: {st.session_state.sc_sex}.\n"
        f"Pre-existing conditions: {st.session_state.sc_conditions or 'None reported'}.\n"
        f"Current symptoms: {', '.join(syms) if syms else 'None specified'}.\n"
        f"Severity: {st.session_state.sc_severity}/10. "
        f"Duration: {st.session_state.sc_duration}.\n\n"
        f"Please provide:\n"
        f"1. Most likely conditions (differential diagnosis)\n"
        f"2. Urgency level: low / medium / high / emergency\n"
        f"3. Recommended next steps\n"
        f"4. Any immediate warning signs to watch for\n"
        f"Respond in clear structured paragraphs."
    )


def _run_analysis():
    """Calls the RAG chain with the compiled query and stores the result."""
    role       = st.session_state.get("current_role", "patient")
    num_chunks = st.session_state.get("num_chunks", 3)
    query      = _build_query()

    # Determine urgency from severity + symptom keywords BEFORE calling chain
    sev  = st.session_state.sc_severity
    syms = " ".join(st.session_state.sc_symptoms).lower()
    if check_emergency(query) or sev >= 9:
        pre_urgency = "emergency"
    elif sev >= 7 or any(k in syms for k in ["chest pain", "shortness of breath", "blurred vision"]):
        pre_urgency = "high"
    elif sev >= 4:
        pre_urgency = "medium"
    else:
        pre_urgency = "low"

    try:
        result = ask(query, role, num_chunks, [])
        st.session_state.sc_result = {
            "answer":   result["answer"],
            "sources":  result.get("sources", []),
            "urgency":  pre_urgency,
            "severity": sev,
        }
    except Exception as e:
        st.session_state.sc_result = {
            "answer":   f"Analysis failed: {e}",
            "sources":  [],
            "urgency":  "unknown",
            "severity": sev,
        }


# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='topbar'>"
    f"  <span class='tb-title'>Symptom Checker</span>"
    f"  <span class='status-dot'>● RAG-powered</span>"
    f"</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:{_mute}; font-size:0.95rem; max-width:600px; margin-bottom:28px;'>"
    f"Answer the guided questions below. The AI will cross-reference your symptoms "
    f"with the medical knowledge base and provide a structured assessment.</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────
# STEP PROGRESS BAR
# ─────────────────────────────────────────────────────────────────
_step_bar(st.session_state.sc_step)

# ─────────────────────────────────────────────────────────────────
# STEP 1 — PATIENT BASICS
# ─────────────────────────────────────────────────────────────────
if st.session_state.sc_step == 1:
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='font-family:{_fh}; color:{_tx}; margin-bottom:20px;'>Patient Information</h3>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown(f"<span class='slabel'>Age</span>", unsafe_allow_html=True)
        age = st.number_input(
            "Age", min_value=1, max_value=120,
            value=st.session_state.sc_age,
            label_visibility="collapsed", key="input_age",
        )
        st.session_state.sc_age = int(age)

    with col_b:
        st.markdown(f"<span class='slabel'>Biological Sex</span>", unsafe_allow_html=True)
        sex_opts = ["Not specified", "Male", "Female", "Other"]
        sex = st.selectbox(
            "Sex", sex_opts,
            index=sex_opts.index(st.session_state.sc_sex),
            label_visibility="collapsed", key="input_sex",
        )
        st.session_state.sc_sex = sex

    st.markdown(f"<span class='slabel' style='margin-top:14px;'>Pre-existing Medical Conditions</span>",
                unsafe_allow_html=True)
    conds = st.text_area(
        "Conditions",
        value=st.session_state.sc_conditions,
        placeholder="e.g. Type 2 Diabetes, Hypertension, Asthma — or leave blank",
        height=90,
        label_visibility="collapsed", key="input_conditions",
    )
    st.session_state.sc_conditions = conds
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    _, btn_col = st.columns([4, 1])
    with btn_col:
        if st.button("Next →", key="step1_next", use_container_width=True):
            st.session_state.sc_step = 2
            st.rerun()

# ─────────────────────────────────────────────────────────────────
# STEP 2 — SYMPTOM SELECTION
# ─────────────────────────────────────────────────────────────────
elif st.session_state.sc_step == 2:
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='font-family:{_fh}; color:{_tx}; margin-bottom:6px;'>Select Your Symptoms</h3>"
        f"<p style='color:{_mute}; font-size:0.84rem; margin-bottom:18px;'>Select all that apply.</p>",
        unsafe_allow_html=True,
    )

    # --- Symptom chip checkboxes in a 3-column grid ---
    # We store selected symptoms as a list in session state.
    selected = set(st.session_state.sc_symptoms)
    cols = st.columns(3)
    for idx, symptom in enumerate(SYMPTOM_LIST):
        with cols[idx % 3]:
            checked = st.checkbox(
                symptom,
                value=(symptom in selected),
                key=f"sym_{symptom}",
            )
            if checked:
                selected.add(symptom)
            else:
                selected.discard(symptom)
    st.session_state.sc_symptoms = list(selected)

    # --- Free text for other symptoms ---
    st.markdown(f"<span class='slabel' style='margin-top:16px;'>Other symptoms (freetext)</span>",
                unsafe_allow_html=True)
    other = st.text_input(
        "Other", value=st.session_state.sc_other,
        placeholder="Describe any other symptoms not listed above…",
        label_visibility="collapsed", key="input_other",
    )
    st.session_state.sc_other = other
    st.markdown("</div>", unsafe_allow_html=True)

    # Show how many selected
    n_sel = len(st.session_state.sc_symptoms)
    if n_sel:
        st.markdown(
            f"<div style='font-size:0.78rem; color:{_acc}; margin:8px 0;'>"
            f"✓ {n_sel} symptom(s) selected: {', '.join(st.session_state.sc_symptoms)}</div>",
            unsafe_allow_html=True,
        )

    back_col, _, next_col = st.columns([1, 3, 1])
    with back_col:
        st.markdown("<div class='ghost-btn'>", unsafe_allow_html=True)
        if st.button("← Back", key="step2_back", use_container_width=True):
            st.session_state.sc_step = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with next_col:
        if st.button("Next →", key="step2_next", use_container_width=True):
            if not st.session_state.sc_symptoms and not st.session_state.sc_other.strip():
                st.warning("Please select at least one symptom.")
            else:
                st.session_state.sc_step = 3
                st.rerun()

# ─────────────────────────────────────────────────────────────────
# STEP 3 — SEVERITY, DURATION, ANALYSIS
# ─────────────────────────────────────────────────────────────────
elif st.session_state.sc_step == 3:
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='font-family:{_fh}; color:{_tx}; margin-bottom:20px;'>Severity & Duration</h3>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<span class='slabel'>Symptom Severity — <b style='color:{_acc};'>"
        f"{st.session_state.sc_severity}/10</b></span>",
        unsafe_allow_html=True,
    )
    sev = st.slider(
        "Severity", 1, 10, st.session_state.sc_severity,
        label_visibility="collapsed", key="sev_slider",
    )
    st.session_state.sc_severity = sev

    # Severity interpretation hint
    _sev_hint = {range(1,4):"Mild — monitoring sufficient",
                 range(4,7):"Moderate — consider seeing a doctor",
                 range(7,9):"Severe — medical attention recommended",
                 range(9,11):"Critical — seek emergency care immediately"}
    _hint_txt = next((v for r, v in _sev_hint.items() if sev in r), "")
    _hint_col = _grn if sev < 4 else (_wbd if sev < 7 else _ebd)
    st.markdown(
        f"<div style='font-size:0.78rem; color:{_hint_col}; margin-bottom:16px;'>"
        f"💡 {_hint_txt}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f"<span class='slabel'>How long have you had these symptoms?</span>",
                unsafe_allow_html=True)
    dur = st.selectbox(
        "Duration", DURATION_OPTIONS,
        index=DURATION_OPTIONS.index(st.session_state.sc_duration),
        label_visibility="collapsed", key="dur_select",
    )
    st.session_state.sc_duration = dur
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    back_col, _, analyse_col = st.columns([1, 2, 2])
    with back_col:
        st.markdown("<div class='ghost-btn'>", unsafe_allow_html=True)
        if st.button("← Back", key="step3_back", use_container_width=True):
            st.session_state.sc_step = 2
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with analyse_col:
        if st.button("🔬  Analyse Symptoms", key="step3_analyse", use_container_width=True):
            with st.spinner("Cross-referencing knowledge base…"):
                _run_analysis()

    # ── RESULTS CARD ─────────────────────────────────────────────
    if st.session_state.sc_result:
        res      = st.session_state.sc_result
        urgency  = res["urgency"]
        severity = res["severity"]

        st.markdown("<br/>", unsafe_allow_html=True)

        # Emergency banner for high-severity cases
        if urgency == "emergency" or severity >= 8:
            st.markdown(
                "<div class='emg-box'>🚨 <strong>EMERGENCY INDICATORS DETECTED.</strong><br>"
                "Please call <strong>115</strong> (Pakistan Rescue) or "
                "<strong>1122</strong> (Punjab) or go to the nearest A&E immediately.<br>"
                "Do not rely on this app in an emergency.</div>",
                unsafe_allow_html=True,
            )
        elif severity >= 7:
            st.markdown(
                "<div class='warn-box'>⚠️ <strong>High severity reported.</strong> "
                "You should seek medical advice promptly. "
                "If symptoms worsen suddenly, call emergency services.</div>",
                unsafe_allow_html=True,
            )

        # Result card
        badge_html = _urgency_badge(urgency)
        st.markdown(
            f"<div class='card'>"
            f"<div style='display:flex; align-items:center; gap:12px; margin-bottom:16px;'>"
            f"  <span style='font-family:{_fh}; font-size:1.1rem; font-weight:700; color:{_tx};'>"
            f"    Clinical Assessment</span>"
            f"  {badge_html}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        with st.chat_message("assistant", avatar="🏥"):
            st.markdown(res["answer"])
            if res.get("sources"):
                with st.expander(f"📎 {len(res['sources'])} evidence source(s)"):
                    for doc in res["sources"]:
                        import os
                        fname   = os.path.basename(doc.metadata.get("source", "PDF"))
                        pg_raw  = doc.metadata.get("page", 0)
                        pg      = (pg_raw + 1) if isinstance(pg_raw, int) else pg_raw
                        preview = doc.page_content.strip().replace("\n", " ")[:160]
                        st.markdown(
                            f"<div class='src-card'>"
                            f"<span class='src-fname'>📄 {fname}</span>"
                            f"<span class='src-page'>p.{pg}</span>"
                            f"<div class='src-prev'>\"{preview}...\"</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        # Start over button
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("<div class='ghost-btn'>", unsafe_allow_html=True)
        if st.button("↺  Start new assessment", key="sc_reset", use_container_width=False):
            for _k, _v in _SC_DEFAULTS.items():
                st.session_state[_k] = _v
            # Clear symptom checkboxes
            for sym in SYMPTOM_LIST:
                if f"sym_{sym}" in st.session_state:
                    del st.session_state[f"sym_{sym}"]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='app-footer'>Symptom assessment is informational only. "
    "It does not replace a clinical examination by a qualified doctor.</div>",
    unsafe_allow_html=True,
)
