"""
theme.py — Aegis Health AI: Shared Design System
=================================================
Every page imports this module to get fully-consistent themed CSS.
Call get_tokens() to get a dict of all colour/font values.
Call inject_css(D) to inject the master CSS block into the page.
"""

import streamlit as st


def get_tokens() -> dict:
    """Returns all colour + font tokens for the currently active theme."""
    T = st.session_state.get("theme", "day")

    if T == "day":
        return dict(
            T="day",
            app_bg="#faf6f0", side_bg="#f2ebe0", surf="#ffffff", surf2="#f7f2ea",
            acc="#c4571a",    acc_h="#a83d10",   green="#2d5a3d",
            gr_bg="rgba(45,90,61,0.10)",
            tx="#1a1208",     mute="#8a7560",    mute2="#b0a090",
            bd="rgba(26,18,8,0.10)",   bd_a="rgba(196,87,26,0.25)",
            in_bg="#f2ebe0",  btn_tx="#ffffff",
            u_bg="#1a1208",   u_tx="#ffffff",
            emg_bg="#fff1f1", emg_bd="#dc2626",  emg_tx="#991b1b",
            warn_bg="#fffbeb",warn_bd="#d97706",  warn_tx="#92400e",
            font_url=(
                "https://fonts.googleapis.com/css2?"
                "family=Playfair+Display:wght@700"
                "&family=DM+Sans:wght@400;500;600&display=swap"
            ),
            fh="'Playfair Display', serif",
            fb="'DM Sans', sans-serif",
        )

    return dict(
        T="night",
        app_bg="#080d1e", side_bg="#060b19", surf="#0d1530", surf2="#111a38",
        acc="#5b8cf7",    acc_h="#3a6ef5",   green="#34d399",
        gr_bg="rgba(52,211,153,0.10)",
        tx="#e8edf8",     mute="#5a6b94",    mute2="#3a4b6a",
        bd="rgba(91,140,247,0.10)",   bd_a="rgba(91,140,247,0.25)",
        in_bg="#0d1530",  btn_tx="#080d1e",
        u_bg="#1e3a8a",   u_tx="#e8edf8",
        emg_bg="rgba(220,38,38,0.12)", emg_bd="#dc2626", emg_tx="#fca5a5",
        warn_bg="rgba(217,119,6,0.10)", warn_bd="#d97706", warn_tx="#fbbf24",
        font_url=(
            "https://fonts.googleapis.com/css2?"
            "family=Space+Grotesk:wght@300;400;500;600;700&display=swap"
        ),
        fh="'Space Grotesk', sans-serif",
        fb="'Space Grotesk', sans-serif",
    )


def inject_css(D: dict):
    """
    Injects the full themed CSS into the current page.
    All dict values are extracted to plain variables first so
    there are no backslashes inside f-string {} expressions
    (Python 3.11 restriction).
    """
    _app  = D["app_bg"];  _side = D["side_bg"]; _surf = D["surf"];   _surf2 = D["surf2"]
    _acc  = D["acc"];     _acch = D["acc_h"];   _grn  = D["green"];  _gr_bg = D["gr_bg"]
    _tx   = D["tx"];      _mute = D["mute"];    _mt2  = D["mute2"]
    _bd   = D["bd"];      _bda  = D["bd_a"];    _inbg = D["in_bg"];  _bntx = D["btn_tx"]
    _ubg  = D["u_bg"];    _utx  = D["u_tx"]
    _ebg  = D["emg_bg"];  _ebd  = D["emg_bd"]; _etx  = D["emg_tx"]
    _wbg  = D["warn_bg"]; _wbd  = D["warn_bd"]; _wtx  = D["warn_tx"]
    _furl = D["font_url"]; _fh  = D["fh"];      _fb   = D["fb"]

    st.markdown(f"""
<style>
@import url('{_furl}');

/* ── Global reset ─────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {{
    font-family      : {_fb}   !important;
    background-color : {_app}  !important;
    color            : {_tx}   !important;
}}

/* ── Kill decoration / toolbar / footer ───────────────────── */
div[data-testid="stDecoration"], div[data-testid="stToolbar"],
footer, #MainMenu {{ display:none !important; height:0 !important; }}

/* ── Header — transparent, visible for sidebar toggle ──────── */
div[data-testid="stHeader"], header[data-testid="stHeader"],
.stApp > header {{
    background:transparent !important; border:none !important;
    position:fixed !important; top:0 !important; left:0 !important;
    height:3rem !important; z-index:999 !important;
    pointer-events:none !important;
}}
div[data-testid="stHeader"] button {{ pointer-events:all !important; }}

/* ── Sidebar EXPAND button — floats on LEFT EDGE when sidebar is closed ── */
/* position:fixed with explicit coordinates ensures it is ALWAYS visible    */
/* and never clipped by the transparent header layer.                       */
button[data-testid="stBaseButton-headerNoPadding"] {{
    position         : fixed           !important;
    left             : 10px            !important;
    top              : 50vh            !important;
    transform        : translateY(-50%) !important;
    z-index          : 99999           !important;
    pointer-events   : all             !important;
    background       : {_surf2}        !important;
    color            : {_acc}          !important;
    border           : 1.5px solid {_bda} !important;
    border-radius    : 12px            !important;
    width            : 32px            !important;
    height           : 48px            !important;
    display          : flex            !important;
    align-items      : center          !important;
    justify-content  : center          !important;
    box-shadow       : 2px 0 14px rgba(0,0,0,0.14) !important;
    transition       : all 0.2s        !important;
}}
button[data-testid="stBaseButton-headerNoPadding"]:hover {{
    background   : {_surf} !important;
    border-color : {_acc}  !important;
    box-shadow   : 4px 0 20px rgba(0,0,0,0.20) !important;
}}
button[data-testid="stBaseButton-headerNoPadding"] svg {{
    fill : {_acc} !important;
    width : 16px  !important;
    height: 16px  !important;
}}

/* ── Sidebar COLLAPSE pill — floats on RIGHT EDGE of sidebar when open ── */
button[data-testid="stSidebarCollapse"] {{
    position         : fixed      !important;
    top              : 50vh       !important;
    transform        : translateY(-50%) !important;
    z-index          : 9999       !important;
    background       : {_surf2}   !important;
    border           : 1.5px solid {_bda} !important;
    border-radius    : 24px       !important;
    width            : 22px       !important;
    height           : 44px       !important;
    display          : flex       !important;
    align-items      : center     !important;
    justify-content  : center     !important;
    box-shadow       : 2px 0 12px rgba(0,0,0,0.10) !important;
    transition       : all 0.2s   !important;
}}
button[data-testid="stSidebarCollapse"] svg {{ fill:{_acc} !important; }}
button[data-testid="stSidebarCollapse"]:hover {{
    background   : {_surf} !important;
    border-color : {_acc}  !important;
}}

/* ── Sidebar background ───────────────────────────────────── */
section[data-testid="stSidebar"], [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] > div {{
    background-color:{_side} !important;
    border-right:1px solid {_bd} !important;
}}
section[data-testid="stSidebar"] * {{ color:{_tx} !important; }}

/* ── Main block container ─────────────────────────────────── */
.main .block-container, [data-testid="stMainBlockContainer"] {{
    background-color:{_app} !important;
    padding:24px 36px 0 36px !important; max-width:100% !important;
}}

/* ── All stButtons (default accent style) ─────────────────── */
.stButton > button {{
    background-color:{_acc} !important; color:{_bntx} !important;
    border:none !important; border-radius:8px !important;
    font-family:{_fb} !important; font-weight:600 !important;
    font-size:0.84rem !important; padding:9px 20px !important;
    transition:background 0.2s, transform 0.15s !important;
}}
.stButton > button:hover {{
    background-color:{_acch} !important; transform:translateY(-1px) !important;
}}

/* ── Toggle/ghost button ─────────────────────────────────── */
.toggle-wrap .stButton > button {{
    background:{_surf2} !important; color:{_acc} !important;
    border:1.5px solid {_bda} !important; border-radius:20px !important;
    font-size:0.8rem !important; padding:6px 16px !important; font-weight:500 !important;
}}
.toggle-wrap .stButton > button:hover {{
    background:{_surf} !important; border-color:{_acc} !important; transform:none !important;
}}

/* ── Ghost / danger button wrappers ──────────────────────── */
.ghost-btn .stButton > button {{
    background:transparent !important; color:{_mute} !important;
    border:1px solid {_bd} !important; font-size:0.8rem !important;
}}
.ghost-btn .stButton > button:hover {{
    color:{_acc} !important; border-color:{_acc} !important; transform:none !important;
}}
.danger-btn .stButton > button {{
    background:rgba(220,38,38,0.10) !important; color:{_ebd} !important;
    border:1px solid {_ebd} !important;
}}
.danger-btn .stButton > button:hover {{
    background:{_ebd} !important; color:#fff !important; transform:none !important;
}}

/* ── Chat input bottom area ───────────────────────────────── */
[data-testid="stBottom"], [data-testid="stBottom"] > *,
[data-testid="stBottom"] > * > *, .stChatFloatingInputContainer,
div[data-testid="stChatInput"], div[data-testid="stChatInput"] > div {{
    background-color:{_app} !important; border-top:1px solid {_bd} !important;
}}
div[data-testid="stChatInput"] textarea {{
    background:{_inbg} !important; color:{_tx} !important;
    border:1px solid {_bda} !important; border-radius:12px !important;
    font-family:{_fb} !important; caret-color:{_acc} !important;
}}
div[data-testid="stChatInput"] textarea::placeholder {{ color:{_mute} !important; opacity:0.7 !important; }}
div[data-testid="stChatInput"] textarea:focus {{
    border-color:{_acc} !important; box-shadow:0 0 0 3px {_bda} !important; outline:none !important;
}}
div[data-testid="stChatInput"] button {{
    background:{_acc} !important; color:{_bntx} !important;
    border-radius:10px !important; border:none !important;
}}

/* ── Chat messages ────────────────────────────────────────── */
[data-testid="stChatMessage"] {{
    background:{_surf} !important; border:1px solid {_bd} !important;
    border-radius:14px !important;
}}
[data-testid="stChatMessage"] p {{ color:{_tx} !important; line-height:1.7 !important; }}

/* ── Expander ─────────────────────────────────────────────── */
[data-testid="stExpander"], [data-testid="stExpander"] > div {{
    background:{_surf2} !important; border:1px solid {_bd} !important; border-radius:10px !important;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] p {{ color:{_mute} !important; font-size:0.8rem !important; }}

/* ── Select / dropdown / text input ─────────────────────── */
[data-baseweb="select"] > div {{
    background:{_inbg} !important; border-color:{_bda} !important; border-radius:8px !important;
}}
[data-baseweb="select"] span {{ color:{_tx} !important; }}
[data-baseweb="select"] [role="listbox"] {{ background:{_surf} !important; }}
[data-baseweb="select"] [role="option"] {{ color:{_tx} !important; }}
[data-baseweb="select"] [role="option"]:hover {{ background:{_surf2} !important; }}
input[type="number"], .stTextInput > div > input, .stTextArea textarea {{
    background:{_inbg} !important; color:{_tx} !important;
    border:1px solid {_bda} !important; border-radius:8px !important;
    font-family:{_fb} !important;
}}
input[type="number"]::placeholder, .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color:{_mute} !important;
}}
input[type="number"]:focus, .stTextInput input:focus, .stTextArea textarea:focus {{
    border-color:{_acc} !important; outline:none !important; box-shadow:0 0 0 3px {_bda} !important;
}}

/* ── Slider track + thumb ─────────────────────────────────── */
[data-baseweb="slider"] [role="slider"] {{
    background:{_acc} !important; border-color:{_acc} !important;
}}

/* ── Progress bar ─────────────────────────────────────────── */
[data-testid="stProgress"] > div {{ background:{_surf2} !important; }}
[data-testid="stProgress"] > div > div {{ background:{_acc} !important; }}

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-thumb {{ background:{_bda}; border-radius:8px; }}
::-webkit-scrollbar-thumb:hover {{ background:{_acc}; }}
::-webkit-scrollbar-track {{ background:transparent; }}

/* ── Divider ──────────────────────────────────────────────── */
hr {{ border:none !important; border-top:1px solid {_bd} !important; margin:14px 0 !important; }}

/* ═══════════════════════════════════════════════════════════
   SHARED COMPONENT CLASSES
   ═══════════════════════════════════════════════════════════ */
h1 {{ font-family:{_fh} !important; font-size:2.8rem !important; font-weight:700 !important;
      letter-spacing:-0.02em; color:{_tx} !important; margin:0 0 10px !important; }}
h2, h3 {{ font-family:{_fh} !important; color:{_tx} !important; }}

/* Logo */
.logo-icon {{ background:{_acc}; color:#fff; width:38px; height:38px; border-radius:8px;
              display:inline-flex; align-items:center; justify-content:center; font-weight:800; font-size:1.1rem; }}

/* Section label */
.slabel {{ font-size:0.6rem; font-weight:700; letter-spacing:1.4px; text-transform:uppercase;
           color:{_mt2}; display:block; margin-bottom:8px; }}

/* Topbar */
.topbar {{ display:flex; align-items:center; gap:12px; padding-bottom:18px;
           border-bottom:1px solid {_bd}; margin-bottom:28px; }}
.tb-title {{ font-size:1rem; font-weight:700; color:{_tx}; }}
.status-dot {{ font-size:0.72rem; color:{_grn}; background:{_gr_bg}; border:1px solid {_grn}33;
               padding:3px 11px; border-radius:20px; font-weight:500; }}
.mode-chip {{ font-size:0.7rem; color:{_mute}; background:{_surf2};
              border:1px solid {_bd}; padding:3px 11px; border-radius:20px; }}

/* Role cards */
.role-card {{ display:flex; align-items:center; gap:10px; padding:10px 14px;
              border-radius:10px; border:1.5px solid {_bd}; margin-bottom:6px; cursor:pointer; }}
.role-card.active {{ border-color:{_acc}; background:{_surf2}; }}
.role-badge-p {{ width:24px; height:24px; border-radius:6px; background:{_acc}; color:#fff;
                 font-size:0.68rem; font-weight:700; display:flex; align-items:center; justify-content:center; }}
.role-badge-d {{ width:24px; height:24px; border-radius:6px; background:{_surf2}; color:{_mute};
                 border:1px solid {_bd}; font-size:0.68rem; font-weight:700;
                 display:flex; align-items:center; justify-content:center; }}
.role-label {{ font-size:0.86rem; font-weight:500; color:{_tx}; }}

/* Metric grid */
.metric-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
.mbox {{ background:{_surf2}; border:1px solid {_bd}; border-radius:10px; padding:12px; }}
.mval {{ font-size:1.22rem; font-weight:700; color:{_acc}; line-height:1; }}
.mval.gr {{ color:{_grn}; }}
.mlbl {{ font-size:0.58rem; text-transform:uppercase; letter-spacing:1.2px; color:{_mt2}; margin-top:3px; }}

/* Chips */
.chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
.chip {{ font-size:0.73rem; color:{_mute}; background:{_surf2}; border:1px solid {_bd};
         padding:4px 11px; border-radius:20px; cursor:pointer; }}
.chip:hover {{ border-color:{_acc}; color:{_acc}; }}

/* Page hero tag */
.hero-tag {{ font-size:0.65rem; font-weight:700; letter-spacing:2.5px; text-transform:uppercase;
             color:{_acc}; display:flex; align-items:center; gap:10px; margin-bottom:14px; }}
.hero-tag::before {{ content:''; display:inline-block; width:28px; height:2px;
                     background:{_acc}; border-radius:2px; flex-shrink:0; }}

/* Generic card */
.card {{ background:{_surf}; border:1px solid {_bd}; border-radius:14px; padding:20px 24px; margin-bottom:14px; }}
.card-sm {{ background:{_surf2}; border:1px solid {_bd}; border-radius:10px; padding:14px 18px; margin-bottom:10px; }}

/* User chat bubble */
.user-row {{ display:flex; justify-content:flex-end; margin-bottom:4px; }}
.user-bubble {{ background:{_ubg}; color:{_utx}; border-radius:14px 14px 3px 14px;
                padding:12px 18px; max-width:80%; font-size:0.93rem; line-height:1.6; }}
.user-meta {{ text-align:right; font-size:0.68rem; color:{_mt2}; margin-bottom:14px; }}

/* Source card */
.src-card {{ border-left:2.5px solid {_acc}; border-radius:0 8px 8px 0;
             padding:9px 13px; margin:5px 0; background:{_app}; }}
.src-fname {{ color:{_acc}; font-weight:600; font-size:0.8rem; }}
.src-page  {{ color:{_mute}; font-size:0.72rem; margin-left:8px; }}
.src-prev  {{ color:{_mute}; font-style:italic; font-size:0.77rem; margin-top:3px; }}

/* Confidence note */
.conf {{ font-size:0.7rem; color:{_mt2}; margin-top:7px; }}

/* Emergency / warning banners */
.emg-box  {{ background:{_ebg}; border:1.5px solid {_ebd}; color:{_etx};
             border-radius:10px; padding:14px 20px; margin-bottom:14px;
             font-weight:600; font-size:0.88rem; line-height:1.65; }}
.warn-box {{ background:{_wbg}; border:1.5px solid {_wbd}; color:{_wtx};
             border-radius:10px; padding:14px 20px; margin-bottom:14px;
             font-size:0.88rem; line-height:1.65; }}

/* Severity badges */
.badge {{ display:inline-block; padding:4px 14px; border-radius:20px;
          font-size:0.75rem; font-weight:700; letter-spacing:0.5px; }}
.badge-low      {{ background:rgba(52,211,153,0.12); color:#059669; border:1px solid #059669; }}
.badge-medium   {{ background:rgba(217,119,6,0.12);  color:#d97706; border:1px solid #d97706; }}
.badge-high     {{ background:rgba(234,88,12,0.12);  color:#ea580c; border:1px solid #ea580c; }}
.badge-emergency {{ background:rgba(220,38,38,0.12); color:{_ebd}; border:1px solid {_ebd}; }}

/* Step progress bar */
.step-bar {{ display:flex; align-items:center; gap:8px; margin-bottom:28px; }}
.step-dot {{ width:28px; height:28px; border-radius:50%; display:flex;
             align-items:center; justify-content:center; font-size:0.72rem; font-weight:700; flex-shrink:0; }}
.step-dot.done   {{ background:{_acc}; color:#fff; }}
.step-dot.active {{ background:{_acc}22; color:{_acc}; border:2px solid {_acc}; }}
.step-dot.idle   {{ background:{_surf2}; color:{_mute}; border:2px solid {_bd}; }}
.step-line {{ flex:1; height:2px; border-radius:2px; }}
.step-line.done {{ background:{_acc}; }}
.step-line.idle {{ background:{_bd}; }}

/* Symptom chip grid (special checked state) */
.sym-chip {{ font-size:0.8rem; font-weight:500; color:{_mute}; background:{_surf2};
             border:1.5px solid {_bd}; padding:6px 14px; border-radius:8px; cursor:pointer;
             transition:all 0.15s; }}
.sym-chip.selected {{ background:{_acc}1a; color:{_acc}; border-color:{_acc}; }}

/* Danger zone */
.danger-zone {{ border:1px solid {_ebd}33; border-radius:12px; padding:18px 22px; margin-top:20px; }}
.danger-title {{ font-size:0.72rem; font-weight:700; color:{_ebd}; letter-spacing:1px;
                 text-transform:uppercase; margin-bottom:6px; }}

/* Footer */
.app-footer {{ text-align:center; font-size:0.7rem; color:{_mt2}; font-style:italic;
               border-top:1px solid {_bd}; padding:14px 0 6px 0; margin-top:24px; }}
</style>
""", unsafe_allow_html=True)


def inject_sidebar_js(D: dict):
    """
    Injects a JavaScript component that watches the sidebar width every 200 ms.
    When the sidebar collapses (width < 50 px) it creates a themed floating
    '▶' pill on the left edge.  Clicking it triggers the native Streamlit
    sidebar-expand button.  The pill disappears automatically when the
    sidebar reopens.

    Why JS instead of CSS?
    The native expand button lives inside `stHeader` and may not exist in
    the DOM at all when collapsed — so CSS :hover / position tricks are
    unreliable.  JS can append a brand-new element to <body> that is
    completely independent of Streamlit's header lifecycle.
    """
    import streamlit.components.v1 as components

    # Theme-aware colours (extracted to plain vars — no backslash in f-string {})
    _acc   = D["acc"]
    _surf2 = D["surf2"]
    _surf  = D["surf"]
    _bda   = D["bd_a"]
    _tx    = D["tx"]

    components.html(f"""
<script>
(function() {{
    // ── colours from current theme ──────────────────────────────
    var ACC   = "{_acc}";
    var SURF2 = "{_surf2}";
    var SURF  = "{_surf}";
    var BDA   = "{_bda}";
    var TX    = "{_tx}";
    var BTN_ID = "aegis-expand-btn";

    function getSidebar() {{
        // st.navigation wraps the sidebar in [data-testid="stSidebar"]
        return window.parent.document.querySelector('[data-testid="stSidebar"]');
    }}

    function getExistingBtn() {{
        return window.parent.document.getElementById(BTN_ID);
    }}

    function createExpandBtn() {{
        var btn = window.parent.document.createElement("button");
        btn.id = BTN_ID;
        btn.title = "Open sidebar";
        btn.innerHTML = "&#9654;";  // ▶
        btn.style.cssText = [
            "position:fixed",
            "left:8px",
            "top:50vh",
            "transform:translateY(-50%)",
            "z-index:2147483647",
            "background:" + SURF2,
            "color:" + ACC,
            "border:1.5px solid " + BDA,
            "border-radius:12px",
            "width:30px",
            "height:50px",
            "cursor:pointer",
            "font-size:13px",
            "display:flex",
            "align-items:center",
            "justify-content:center",
            "box-shadow:3px 0 16px rgba(0,0,0,0.18)",
            "transition:all 0.2s ease"
        ].join(";");

        btn.onmouseenter = function() {{
            btn.style.background = SURF;
            btn.style.borderColor = ACC;
            btn.style.boxShadow = "5px 0 22px rgba(0,0,0,0.26)";
        }};
        btn.onmouseleave = function() {{
            btn.style.background = SURF2;
            btn.style.borderColor = BDA;
            btn.style.boxShadow = "3px 0 16px rgba(0,0,0,0.18)";
        }};

        btn.onclick = function() {{
            // Try every selector Streamlit uses for the expand/collapse trigger
            var native = (
                window.parent.document.querySelector('[data-testid="stBaseButton-headerNoPadding"]') ||
                window.parent.document.querySelector('[data-testid="stSidebarCollapse"]') ||
                window.parent.document.querySelector('[data-testid="stHeader"] button') ||
                window.parent.document.querySelector('button[title="Open sidebar"]') ||
                window.parent.document.querySelector('button[title="Show sidebar"]')
            );
            if (native) {{
                native.click();
            }}
        }};

        window.parent.document.body.appendChild(btn);
        return btn;
    }}

    function tick() {{
        var sidebar = getSidebar();
        var existing = getExistingBtn();

        if (!sidebar) {{
            // Sidebar element not in DOM yet — remove stale button if any
            if (existing) existing.remove();
            return;
        }}

        // Consider sidebar "collapsed" when its visible width is tiny
        var collapsed = sidebar.getBoundingClientRect().width < 60;

        if (collapsed && !existing) {{
            createExpandBtn();
        }} else if (!collapsed && existing) {{
            existing.remove();
        }}
    }}

    // Start watching immediately, then every 200 ms
    tick();
    setInterval(tick, 200);
}})();
</script>
""", height=0, scrolling=False)
