"""
Tiny lexicon-based sentiment scorer. Works on English, Telugu-in-Latin-script
and simple Telugu unicode words -- good enough to turn a message into a
numeric "frustration signal" feature for the escalation model. Swap for a
proper multilingual sentiment model (e.g. XLM-R fine-tuned) later.
"""
import re

NEGATIVE_WORDS = {
    "angry", "furious", "worst", "useless", "horrible", "frustrated",
    "unacceptable", "scam", "never", "cancel", "sue", "complaint", "bad",
    "poor", "waste", "cheated", "fraud", "disgusting", "pathetic",
    "kastam", "chetha", "chala problem", "issue", "లేదు",
    "పనికిరాదు", "మోసం", "కోపం", "irritating", "annoying",
    "disappointed", "again and again", "every time", "hours", "days",
    "no response", "not working", "not resolved",
}

# A much narrower list of genuinely angry/insulting language, used only to
# fast-track escalation past the normal 1-2-3 stage flow. Deliberately
# excludes plain problem-description phrases like "not working" or
# "issue" -- reporting that something is broken is not the same as being
# angry about it, and the two should not be treated the same way.
FRUSTRATION_WORDS = {
    "angry", "furious", "worst", "useless", "horrible", "unacceptable",
    "scam", "sue", "disgusting", "pathetic", "fraud", "cheated",
    "waste of time", "ridiculous", "terrible", "hopeless", "మోసం", "కోపం",
}

POSITIVE_WORDS = {
    "thanks", "thank you", "great", "good", "happy", "resolved", "helpful",
    "appreciate", "excellent", "బాగుంది", "సరే", "ok", "fine", "perfect",
}

SHOUTING_PATTERN = re.compile(r"[A-Z]{4,}")
MULTI_EXCLAIM = re.compile(r"!{2,}")


def sentiment_score(text: str) -> float:
    """Returns a polarity score roughly in [-1, 1]. Negative = frustrated."""
    lower = text.lower()
    neg_hits = sum(1 for w in NEGATIVE_WORDS if w in lower)
    pos_hits = sum(1 for w in POSITIVE_WORDS if w in lower)

    score = (pos_hits - neg_hits) / max(1, pos_hits + neg_hits)
    if MULTI_EXCLAIM.search(text):
        score -= 0.25
    if SHOUTING_PATTERN.search(text):
        score -= 0.2

    return max(-1.0, min(1.0, score))


def negative_word_count(text: str) -> int:
    lower = text.lower()
    return sum(1 for w in NEGATIVE_WORDS if w in lower)


def has_strong_frustration(text: str) -> bool:
    """True only for genuinely angry/insulting messages -- explicit anger
    words, ALL-CAPS shouting, or repeated exclamation marks. A plain
    problem report like 'my internet is not working' should NOT trigger
    this, even though it's negative in tone; it's just a description."""
    lower = text.lower()
    if any(w in lower for w in FRUSTRATION_WORDS):
        return True
    if MULTI_EXCLAIM.search(text):
        return True
    if SHOUTING_PATTERN.search(text):
        return True
    return False
