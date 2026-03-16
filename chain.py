"""
chain.py — Phase 5: RAG Chain with Memory + Role-Aware Prompts
===============================================================
Upgraded from Phase 3 to support conversation memory.

Architecture:
  1. User query + full chat history → LLM condenses into a standalone question
  2. Standalone question → FAISS retrieves top-k relevant chunks
  3. Chunks + standalone question + role prompt → Gemini 2.5 Flash
  4. Returns answer + source documents used

Key upgrade from Phase 3:
  - Now accepts `chat_history` (list of (human, ai) string tuples)
  - Uses LangChain LCEL pipeline with MessagesPlaceholder for memory
  - Module-level caching: embeddings & vectorstore load ONCE per process
"""

import os
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings       # modern, non-deprecated
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

load_dotenv()

# ─────────────────────────────────────────────────────────────────
# Module-level cache: load ONCE, reuse forever
# Without this, Streamlit would reload the 80MB model on every click
# ─────────────────────────────────────────────────────────────────
_embeddings_cache  = None
_vectorstore_cache = None
_llm_cache         = None


# ═════════════════════════════════════════════════════════════════
# ROLE-AWARE SYSTEM PROMPTS
# {context}  = text chunks retrieved from FAISS
# Conversation history is handled via MessagesPlaceholder, not here
# ═════════════════════════════════════════════════════════════════

DOCTOR_SYSTEM = """You are a specialized clinical AI assistant supporting medical professionals.
Your answers must be:
- Technically precise with proper medical terminology
- Structured with clear sections (e.g., Pathophysiology, Diagnosis, Treatment Options)
- Grounded ONLY in the retrieved medical context provided below
- If the context does not contain enough information, explicitly state:
  "The provided literature does not contain sufficient detail on this topic. Refer to current clinical guidelines."

Retrieved Medical Literature:
{context}"""


PATIENT_SYSTEM = """You are a friendly and caring AI health assistant speaking with a patient.
Your answers must be:
- Written in simple, everyday language — absolutely no medical jargon
- Warm, reassuring, and practical
- Grounded ONLY in the retrieved health document context provided below  
- If the context has no relevant information, say:
  "I'm sorry, I couldn't find information about that in my health documents. Please speak to your doctor."
- Always end your answer with this exact line:
  "⚕️ Remember: this information is educational only. Always consult a real doctor for personal medical advice."

Retrieved Health Information:
{context}"""


# ═════════════════════════════════════════════════════════════════
# HELPER — get or create cached components
# ═════════════════════════════════════════════════════════════════

def _get_vectorstore(vectorstore_dir: str = "vectorstore") -> FAISS:
    """Returns the cached FAISS vector store, loading it on first call."""
    global _embeddings_cache, _vectorstore_cache

    if _vectorstore_cache is not None:
        return _vectorstore_cache

    if not os.path.exists(vectorstore_dir):
        raise FileNotFoundError(
            f"Vector store not found at '{vectorstore_dir}/'.\n"
            "Please run 'python ingest.py' first."
        )

    print("🧠 Loading HuggingFace Embeddings (all-MiniLM-L6-v2) on CPU...")
    _embeddings_cache = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    print("📂 Loading FAISS index from vectorstore/...")
    _vectorstore_cache = FAISS.load_local(
        vectorstore_dir,
        _embeddings_cache,
        allow_dangerous_deserialization=True
    )
    print("   ✅ Vector store ready.\n")
    return _vectorstore_cache


def _get_llm() -> ChatGoogleGenerativeAI:
    """Returns the cached Gemini 2.5 Flash LLM instance."""
    global _llm_cache

    if _llm_cache is not None:
        return _llm_cache

    # Try both names for maximum compatibility (local .env vs server Secrets)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "API Key not found. Please ensure 'GEMINI_API_KEY' or 'GOOGLE_API_KEY' "
            "is set in your environment or Streamlit Secrets."
        )

    _llm_cache = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,          # low = more factual, less creative
        google_api_key=api_key
    )
    return _llm_cache


def _history_to_messages(chat_history: list) -> list:
    """
    Converts our simple (human_str, ai_str) tuple format into
    LangChain message objects that can be inserted into a ChatPromptTemplate.

    Why tuples? They are JSON-serializable and easy to store in
    st.session_state. LangChain's LCEL prompts need Message objects.

    Args:
        chat_history: list of (human_text, ai_text) tuples from session state
    Returns:
        list of HumanMessage / AIMessage objects
    """
    messages = []
    for human_text, ai_text in chat_history:
        messages.append(HumanMessage(content=human_text))
        messages.append(AIMessage(content=ai_text))
    return messages


# ═════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ═════════════════════════════════════════════════════════════════

def ask(
    query: str,
    role: str = "patient",
    num_chunks: int = 3,
    chat_history: list = None   # list of (human_str, ai_str) tuples
) -> dict:
    """
    Full RAG + Memory pipeline. Accepts conversation history so Gemini
    can answer follow-up questions without needing context re-stated.

    HOW MEMORY WORKS (concrete example):
        Message 1 — User:  "I have Type 2 diabetes"
                    Gemini: "I see, Type 2 diabetes involves..."
        Message 2 — User:  "what foods should I avoid?"
                    → chat_history = [("I have Type 2 diabetes", "I see, Type 2...")]
                    → Gemini sees the history + new question
                    → Answers "what foods should I avoid?" IN THE CONTEXT OF DIABETES
                    → Without memory, Gemini would ask "avoid for what condition?"

    Args:
        query:        The user's current question
        role:         "doctor" or "patient" — switches the system prompt
        num_chunks:   Number of FAISS results to retrieve (k)
        chat_history: Prior conversation as [(human, ai), ...] tuples

    Returns:
        {
            "answer":  str — Gemini's response
            "sources": list[Document] — chunks pulled from FAISS
            "role":    str — the role used
        }
    """
    if chat_history is None:
        chat_history = []

    # 1. Load cached components
    vectorstore = _get_vectorstore()
    llm = _get_llm()

    # 2. Create the retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": num_chunks})

    # 3. Convert history tuples → LangChain message objects
    history_messages = _history_to_messages(chat_history)

    # 4. Retrieve relevant source documents (kept so we can return them)
    source_docs = retriever.invoke(query)

    # 5. Hallucination guard — return a polite refusal if FAISS finds nothing
    if not source_docs:
        return {
            "answer": (
                "I could not find relevant information in the knowledge base for this question. "
                "Please consult a qualified medical professional."
            ),
            "sources": [],
            "role": role
        }

    # 6. Format retrieved chunks into one text block
    context_text = "\n\n---\n\n".join(doc.page_content for doc in source_docs)

    # 7. Select the correct system prompt
    system_prompt = DOCTOR_SYSTEM if role == "doctor" else PATIENT_SYSTEM

    # 8. Build the prompt template with memory slot
    #    MessagesPlaceholder injects the full chat history as alternating
    #    HumanMessage / AIMessage objects so Gemini sees the conversation.
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),   # ← memory lives here
        ("human", "{question}"),
    ])

    # 9. Build the LCEL chain
    #    We manually inject context_text and history_messages rather than
    #    using a retriever inside the chain so source_docs stay accessible.
    chain = prompt | llm | StrOutputParser()

    # 10. Invoke the chain
    print(f"  ✅ Found {len(source_docs)} chunks. Sending to Gemini 2.5 Flash...")
    answer = chain.invoke({
        "context":      context_text,
        "chat_history": history_messages,
        "question":     query,
    })

    return {
        "answer":  answer,
        "sources": source_docs,
        "role":    role
    }


# ─────────────────────────────────────────────────────────────────
# MANUAL TEST BLOCK — run with: python chain.py
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    SEP = "=" * 60

    print(f"\n{SEP}")
    print("  TEST 1: Doctor mode — no history")
    print(SEP)
    r1 = ask("What are the treatment options for Type 2 diabetes?", role="doctor")
    print(r1["answer"])
    print(f"\n📚 Sources: {[os.path.basename(d.metadata.get('source','?')) for d in r1['sources']]}")

    # ── Memory test ───────────────────────────────────────────────
    # Simulate: user said "I have diabetes" first, then asks follow-up
    prior_history = [
        ("I have been diagnosed with Type 2 diabetes.", r1["answer"])
    ]

    print(f"\n{SEP}")
    print("  TEST 2: Patient mode — WITH memory (follow-up question)")
    print(SEP)
    r2 = ask(
        query="What foods should I avoid?",   # No mention of diabetes!
        role="patient",
        chat_history=prior_history            # Gemini remembers the context
    )
    print(r2["answer"])
    print(f"\n📚 Sources: {[os.path.basename(d.metadata.get('source','?')) for d in r2['sources']]}")

    print(f"\n{SEP}")
    print("🎉 Memory test complete!")
