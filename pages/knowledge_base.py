"""
pages/knowledge_base.py — Knowledge Base Manager
=================================================
Document management dashboard for the FAISS knowledge base.

Features:
  • Metrics row: PDFs, chunks, last rebuild time, model name
  • Document table with file size, pages, date added, remove button
  • Drag-and-drop PDF uploader
  • Rebuild knowledge base button (runs ingest.py pipeline)
  • Live FAISS search test (type a query, see top-3 chunks)
  • Danger zone: clear all documents + index
"""

import os
import sys
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from theme import get_tokens

# Try to import pypdf for page counts (installed with LangChain)
try:
    from pypdf import PdfReader
    _PYPDF = True
except ImportError:
    _PYPDF = False

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
DATA_DIR      = BASE_DIR / "data"
VS_DIR        = BASE_DIR / "vectorstore"
INGEST_SCRIPT = BASE_DIR / "ingest.py"
STATS_FILE    = BASE_DIR / "kb_stats.json"   # written by ingest.py or we create it here

DATA_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# THEME TOKENS
# ─────────────────────────────────────────────────────────────────
D     = get_tokens()
_acc  = D["acc"];   _tx   = D["tx"];   _mute = D["mute"]
_bd   = D["bd"];    _bda  = D["bd_a"]; _surf = D["surf"]
_surf2 = D["surf2"];_app  = D["app_bg"]; _mt2 = D["mute2"]
_fb   = D["fb"];    _fh   = D["fh"];   _grn  = D["green"]
_ebg  = D["emg_bg"]; _ebd = D["emg_bd"]; _etx = D["emg_tx"]
_bntx = D["btn_tx"]

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
for _k, _v in {
    "kb_confirm_clear": False,  # confirmation gate for Danger Zone
    "kb_rebuild_log":   "",     # last rebuild output
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def _all_pdfs() -> list[Path]:
    """Returns a sorted list of all PDF paths under DATA_DIR."""
    return sorted(DATA_DIR.rglob("*.pdf"))


def _page_count(path: Path) -> str:
    if not _PYPDF:
        return "—"
    try:
        return str(len(PdfReader(str(path)).pages))
    except Exception:
        return "err"


def _file_size(path: Path) -> str:
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 ** 2:.1f} MB"


def _date_added(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _vs_last_built() -> str:
    """Returns the last modification time of the vectorstore folder."""
    if not VS_DIR.exists():
        return "Never"
    ts = VS_DIR.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _chunk_count() -> int:
    """Tries to load the FAISS index and return its ntotal."""
    try:
        import faiss
        idx = faiss.read_index(str(VS_DIR / "index.faiss"))
        return int(idx.ntotal)
    except Exception:
        return 0


def _run_rebuild():
    """Runs ingest.py as a subprocess and captures output."""
    result = subprocess.run(
        [sys.executable, str(INGEST_SCRIPT)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return (result.stdout + result.stderr).strip()


def _search_faiss(query: str, k: int = 3):
    """Runs a direct FAISS similarity search and returns matching docs."""
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    db   = FAISS.load_local(str(VS_DIR), embeddings, allow_dangerous_deserialization=True)
    docs = db.similarity_search(query, k=k)
    return docs


# ─────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='topbar'>"
    f"  <span class='tb-title'>Knowledge Base Manager</span>"
    f"  <span class='status-dot'>● FAISS Index</span>"
    f"</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:{_mute}; font-size:0.95rem; max-width:640px; margin-bottom:28px;'>"
    f"Manage the medical PDF library that powers your RAG pipeline. "
    f"Upload new documents, rebuild the index, and test retrieval quality here.</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────
# 1. METRICS ROW
# ─────────────────────────────────────────────────────────────────
all_pdfs     = _all_pdfs()
n_pdfs       = len(all_pdfs)
n_chunks     = _chunk_count()
last_built   = _vs_last_built()
model_name   = "all-MiniLM-L6-v2"

st.markdown("<span class='slabel'>Knowledge Base Metrics</span>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
for col, val, lbl in [
    (m1, str(n_pdfs),       "PDF Documents"),
    (m2, f"{n_chunks:,}",   "Indexed Chunks"),
    (m3, last_built,        "Last Rebuilt"),
    (m4, model_name,        "Embeddings Model"),
]:
    with col:
        st.markdown(
            f"<div class='mbox'>"
            f"  <div class='mval' style='font-size:1.1rem;'>{val}</div>"
            f"  <div class='mlbl'>{lbl}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("<hr/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 2. DOCUMENT TABLE
# ─────────────────────────────────────────────────────────────────
st.markdown("<span class='slabel'>Document Library</span>", unsafe_allow_html=True)

if not all_pdfs:
    st.markdown(
        f"<div class='card-sm' style='color:{_mute}; font-size:0.88rem;'>"
        f"No PDFs found in <code>data/</code>. Upload documents below.</div>",
        unsafe_allow_html=True,
    )
else:
    # Table header
    h1, h2, h3, h4, h5 = st.columns([4, 1.5, 1, 1.5, 1])
    for col, label in [(h1,"Filename"),(h2,"Size"),(h3,"Pages"),(h4,"Date Added"),(h5,"")]:
        with col:
            st.markdown(
                f"<div style='font-size:0.6rem; font-weight:700; text-transform:uppercase;"
                f"letter-spacing:1px; color:{_mt2}; padding-bottom:6px; border-bottom:1px solid {_bd};'>"
                f"{label}</div>",
                unsafe_allow_html=True,
            )

    # Table rows
    for pdf in all_pdfs:
        rel   = str(pdf.relative_to(DATA_DIR))
        fname = rel
        r1, r2, r3, r4, r5 = st.columns([4, 1.5, 1, 1.5, 1])
        with r1:
            st.markdown(
                f"<div style='font-size:0.82rem; color:{_tx}; padding:10px 0;'>📄 {fname}</div>",
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                f"<div style='font-size:0.82rem; color:{_mute}; padding:10px 0;'>{_file_size(pdf)}</div>",
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                f"<div style='font-size:0.82rem; color:{_mute}; padding:10px 0;'>{_page_count(pdf)}</div>",
                unsafe_allow_html=True,
            )
        with r4:
            st.markdown(
                f"<div style='font-size:0.82rem; color:{_mute}; padding:10px 0;'>{_date_added(pdf)}</div>",
                unsafe_allow_html=True,
            )
        with r5:
            # Unique key per file so there are no duplicate-key errors
            safe_key = "del_" + str(pdf.name).replace(".", "_").replace("-", "_").replace(" ", "_")[:40]
            st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
            if st.button("✕", key=safe_key, help=f"Remove {pdf.name}"):
                pdf.unlink()
                st.success(f"Removed {pdf.name}. Rebuild the index to apply changes.")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 3. FILE UPLOADER
# ─────────────────────────────────────────────────────────────────
st.markdown("<span class='slabel'>Upload New Documents</span>", unsafe_allow_html=True)
st.markdown(
    f"<p style='font-size:0.82rem; color:{_mute}; margin-bottom:10px;'>"
    f"Files are saved to <code>data/uploads/</code>. "
    f"Rebuild the index after uploading to make them searchable.</p>",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Upload PDFs", type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key="kb_uploader",
)

if uploaded:
    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    saved = []
    for f in uploaded:
        dest = upload_dir / f.name
        dest.write_bytes(f.read())
        saved.append(f.name)
    st.success(f"✅  Saved {len(saved)} file(s): {', '.join(saved)}")
    st.info("Click **Rebuild Knowledge Base** below to index the new documents.")

st.markdown("<hr/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 4. REBUILD BUTTON
# ─────────────────────────────────────────────────────────────────
st.markdown("<span class='slabel'>Rebuild Knowledge Base</span>", unsafe_allow_html=True)
st.markdown(
    f"<p style='font-size:0.82rem; color:{_mute}; margin-bottom:12px;'>"
    f"Runs <code>ingest.py</code>: loads all PDFs, rechunks, re-embeds, "
    f"and overwrites the FAISS index in <code>vectorstore/</code>.</p>",
    unsafe_allow_html=True,
)

if st.button("⚙️  Rebuild Knowledge Base", key="kb_rebuild"):
    bar = st.progress(0, text="Starting rebuild…")
    bar.progress(10, text="Loading PDF documents from data/…")

    try:
        log = _run_rebuild()
        bar.progress(100, text="Rebuild complete! ✅")
        st.session_state.kb_rebuild_log = log
        st.success("Knowledge base rebuilt successfully. Restart the app to load the new index.")
    except subprocess.TimeoutExpired:
        bar.progress(100, text="Timed out.")
        st.error("Rebuild timed out after 5 minutes. Try reducing the number of documents.")
    except Exception as e:
        bar.progress(100, text="Failed.")
        st.error(f"Rebuild failed: {e}")

if st.session_state.kb_rebuild_log:
    with st.expander("📋 Last rebuild log"):
        st.code(st.session_state.kb_rebuild_log, language="text")

st.markdown("<hr/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 5. LIVE FAISS SEARCH TEST
# ─────────────────────────────────────────────────────────────────
st.markdown("<span class='slabel'>Test Knowledge Retrieval</span>", unsafe_allow_html=True)
st.markdown(
    f"<p style='font-size:0.82rem; color:{_mute}; margin-bottom:10px;'>"
    f"Type any medical query to see the top 3 chunks retrieved from the FAISS index.</p>",
    unsafe_allow_html=True,
)

search_query = st.text_input(
    "Search", placeholder="e.g. symptoms of Type 2 diabetes",
    label_visibility="collapsed", key="kb_search",
)

if search_query.strip():
    with st.spinner("Searching index…"):
        try:
            docs = _search_faiss(search_query.strip(), k=3)
            st.markdown(
                f"<div style='font-size:0.82rem; color:{_acc}; margin-bottom:10px;'>"
                f"✓ Top {len(docs)} chunk(s) retrieved</div>",
                unsafe_allow_html=True,
            )
            for i, doc in enumerate(docs):
                import os as _os
                fname   = _os.path.basename(doc.metadata.get("source", "Unknown"))
                pg_raw  = doc.metadata.get("page", 0)
                pg      = (pg_raw + 1) if isinstance(pg_raw, int) else pg_raw
                preview = doc.page_content.strip().replace("\n", " ")

                st.markdown(
                    f"<div class='card-sm'>"
                    f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>"
                    f"  <span style='font-size:0.7rem; font-weight:700; color:{_acc}; "
                    f"       background:{_acc}18; padding:2px 10px; border-radius:20px;'>#{i+1}</span>"
                    f"  <span class='src-fname'>📄 {fname}</span>"
                    f"  <span class='src-page'>p.{pg}</span>"
                    f"</div>"
                    f"<div style='font-size:0.82rem; color:{_mute}; font-style:italic;"
                    f"     line-height:1.6; border-left:2px solid {_acc}; padding-left:10px;'>"
                    f"{preview[:300]}{'…' if len(preview) > 300 else ''}"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        except FileNotFoundError:
            st.warning("⚠️  Vector store not found. Please rebuild the knowledge base first.")
        except Exception as e:
            st.error(f"Search error: {e}")

st.markdown("<hr/>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 6. DANGER ZONE
# ─────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='danger-zone'>"
    f"  <div class='danger-title'>⚠  Danger Zone</div>"
    f"  <p style='font-size:0.84rem; color:{_mute}; margin-bottom:14px;'>"
    f"  This will permanently delete <strong>all PDF documents</strong> from <code>data/</code> "
    f"  and clear the <strong>FAISS vectorstore</strong>. This cannot be undone.</p>",
    unsafe_allow_html=True,
)

if not st.session_state.kb_confirm_clear:
    st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
    if st.button("🗑  Clear all documents & index", key="kb_danger_ask"):
        st.session_state.kb_confirm_clear = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("⚠️  **Are you absolutely sure?** This will delete **all documents and the index**.")
    col_yes, col_no, _ = st.columns([1, 1, 4])
    with col_yes:
        st.markdown("<div class='danger-btn'>", unsafe_allow_html=True)
        if st.button("✓ Yes, clear everything", key="kb_danger_confirm"):
            # Delete all PDFs
            for pdf in DATA_DIR.rglob("*.pdf"):
                pdf.unlink()
            # Delete vectorstore contents
            if VS_DIR.exists():
                shutil.rmtree(str(VS_DIR))
            st.session_state.kb_confirm_clear = False
            st.success("✅  All documents and the FAISS index have been cleared.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col_no:
        st.markdown("<div class='ghost-btn'>", unsafe_allow_html=True)
        if st.button("✕ Cancel", key="kb_danger_cancel"):
            st.session_state.kb_confirm_clear = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='app-footer'>Knowledge base operations affect the entire application. "
    "Always rebuild after adding or removing documents.</div>",
    unsafe_allow_html=True,
)
