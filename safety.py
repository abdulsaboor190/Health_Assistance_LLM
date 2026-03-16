"""
safety.py — Phase 5: Input Safety & Emergency Triage Layer
============================================================
This module is the responsible-AI gatekeeper.
It runs BEFORE the query ever reaches the LLM or FAISS.

Two exported functions:
    check_emergency(text)     → True if life-threatening emergency detected
    check_unsafe_input(text)  → True if input should be blocked entirely
"""

import re


# ═════════════════════════════════════════════════════════════════
# EMERGENCY KEYWORDS — trigger a red alert but STILL answer
# The app shows the emergency banner AND then generates an answer.
# ═════════════════════════════════════════════════════════════════
EMERGENCY_KEYWORDS = [
    # Cardiac
    "chest pain", "chest tightness", "heart attack", "cardiac arrest",
    "heart failure", "my heart is racing", "palpitations",
    # Respiratory
    "can't breathe", "cannot breathe", "difficulty breathing",
    "shortness of breath", "not breathing", "stopped breathing",
    "choking", "airway blocked",
    # Neurological
    "stroke", "face drooping", "unable to speak", "sudden numbness",
    "loss of consciousness", "unconscious", "passed out", "seizure",
    "convulsing", "convulsion", "fits",
    # Bleeding & trauma
    "severe bleeding", "bleeding out", "hemorrhage", "blood won't stop",
    "deep wound", "loss of blood",
    # Allergic
    "anaphylaxis", "severe allergic reaction", "throat swelling",
    "tongue swelling", "epipen",
    # Mental health crisis
    "suicide", "suicidal", "want to kill myself", "end my life",
    "self harm", "self-harm", "overdose", "took too many pills",
    "drug overdose",
    # Other emergencies
    "poisoning", "not responsive", "unresponsive",
    "someone collapsed", "fell unconscious",
]


# ═════════════════════════════════════════════════════════════════
# UNSAFE / BLOCKED KEYWORDS — do NOT answer these at all
# ═════════════════════════════════════════════════════════════════
UNSAFE_PATTERNS = [
    # Self-medication with prescription drugs
    r"how much \w+ (can|should) i take",
    r"what (dose|dosage) of \w+ (can|should) i (take|use)",
    r"prescribe me",
    r"prescription (for|drug|medication)",
    r"give me a prescription",

    # Self-harm / harm to others
    r"how (to|do i) (harm|hurt|kill|injure) (myself|someone|my|a person)",
    r"ways to (hurt|harm|kill|injure|attack)",
    r"method(s)? to (die|commit suicide|end (my|a) life)",

    # Demanding diagnoses or replacing doctors
    r"diagnose me with",
    r"tell me (exactly|for sure|definitely) what (disease|condition|illness) i have",
    r"you are (my|a) doctor",
    r"replace (my|a) doctor",
    r"i don.*t need a doctor",

    # Clearly off-topic / abusive
    r"(sex|porn|explicit|nude|naked).*health",
    r"\b(hack|scam|fraud|steal|illegal)\b",
]

# Compile unsafe patterns once at import time for speed
_UNSAFE_RE = [re.compile(p, re.IGNORECASE) for p in UNSAFE_PATTERNS]


def check_emergency(user_input: str) -> bool:
    """
    Checks whether the user's message sounds like a life-threatening emergency.

    This check is CASE-INSENSITIVE (catches "Chest Pain", "CHEST PAIN", etc.)

    Returns:
        True  → emergency detected → show red banner BEFORE the answer
        False → no emergency detected → proceed normally

    Example:
        check_emergency("I have severe chest pain") → True
        check_emergency("What foods help with blood pressure?") → False
    """
    # Normalize: lowercase and strip extra whitespace for reliable matching
    normalized = user_input.lower().strip()

    for keyword in EMERGENCY_KEYWORDS:
        if keyword in normalized:
            return True

    return False


def check_unsafe_input(user_input: str) -> bool:
    """
    Checks whether the user's message should be BLOCKED entirely.
    If True, the app must NOT call the LLM and must show a polite refusal.

    This catches:
      - Requests for specific drug dosages for self-medication
      - Requests to harm self or others
      - Demands to diagnose or replace a doctor
      - Clearly abusive or off-topic content

    Returns:
        True  → block this request, show polite refusal
        False → safe to proceed to the RAG chain

    Example:
        check_unsafe_input("diagnose me with cancer") → True
        check_unsafe_input("What are symptoms of flu?") → False
    """
    normalized = user_input.lower().strip()

    for pattern in _UNSAFE_RE:
        if pattern.search(normalized):
            return True

    return False


# ─────────────────────────────────────────────────────────────────
# MANUAL TESTING BLOCK — run with: python safety.py
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        # Expected: EMERGENCY
        ("I think I'm having a heart attack",           "EMERGENCY"),
        ("My friend is unconscious and not breathing",  "EMERGENCY"),
        ("She's having a seizure",                      "EMERGENCY"),
        ("CHEST PAIN really bad",                       "EMERGENCY"),
        ("I want to kill myself",                       "EMERGENCY"),
        # Expected: BLOCKED
        ("How much ibuprofen can I take?",              "BLOCKED"),
        ("Prescribe me something for my pain",          "BLOCKED"),
        ("Diagnose me with diabetes",                   "BLOCKED"),
        ("You are my doctor now",                       "BLOCKED"),
        ("How do I harm myself",                        "BLOCKED"),
        # Expected: SAFE
        ("What are the symptoms of diabetes?",          "SAFE"),
        ("How does insulin work?",                      "SAFE"),
        ("What foods help lower blood pressure?",       "SAFE"),
        ("Explain first aid for a burn",                "SAFE"),
    ]

    print("\n" + "=" * 60)
    print("  🛡️  SAFETY MODULE MANUAL TEST")
    print("=" * 60)
    all_passed = True
    for text, expected in test_cases:
        if expected == "EMERGENCY":
            result = "EMERGENCY" if check_emergency(text) else "SAFE"
        elif expected == "BLOCKED":
            result = "BLOCKED" if check_unsafe_input(text) else "SAFE"
        else:
            is_emg  = check_emergency(text)
            is_unsafe = check_unsafe_input(text)
            result = "EMERGENCY" if is_emg else ("BLOCKED" if is_unsafe else "SAFE")

        passed = result == expected
        if not passed:
            all_passed = False
        status = "✅" if passed else "❌"
        print(f"{status} [{expected:9s}] '{text[:52]}'")

    print("-" * 60)
    print("✅ All tests passed!" if all_passed else "❌ Some tests FAILED — review UNSAFE_PATTERNS / EMERGENCY_KEYWORDS")
