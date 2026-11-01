"""
Feature: multilingual + code-mixed language support.

Covers English, Hindi, Tamil, Kannada, and Telugu -- both native script
and "romanized code-mixed" typing (e.g. Tenglish, Hinglish, Tanglish,
Kanglish: regional words typed in Latin letters mixed with English).

Two jobs:
  1. Figure out what language(s) the customer is actually typing in.
     Plain langdetect handles native scripts reasonably well but is poor
     at romanized code-mixed text, so we check for that ourselves first
     using per-language marker word lists.
  2. Translate the message to English for the NLU/escalation pipeline, and
     translate the bot's reply back -- via deep-translator (Google Translate
     under the hood). This needs internet access on the machine running the
     backend; if it's unavailable, we fail gracefully and just pass text
     through untranslated rather than crashing the request.

Adding another language later is just adding one more entry to
LANGUAGE_PROFILES below -- nothing else needs to change.
"""
import re
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0  # deterministic langdetect results

LANGUAGE_PROFILES = {
    "te": {
        "label": "Telugu",
        "unicode": re.compile(r"[\u0C00-\u0C7F]"),
        "romanized": {
            "naaku", "naku", "naa", "meeru", "meku", "ledu", "undi", "kavali", "cheyandi",
            "chesa", "chesanu", "enduku", "ela", "avutledu", "avvatledu", "vachindi",
            "padindi", "chala", "kastam", "sare", "akkada", "ikkada", "nenu", "idi",
            "adi", "yenti", "enti", "gaa", "meeku", "lo", "ki", "ni",
        },
    },
    "hi": {
        "label": "Hindi",
        "unicode": re.compile(r"[\u0900-\u097F]"),
        "romanized": {
            "hai", "nahi", "kya", "mera", "aapka", "kaise", "kyun", "matlab",
            "chahiye", "raha", "rahi", "abhi", "kab", "kaha", "acha", "theek",
            "bilkul", "karo", "nahin", "mujhe", "aapko", "sahi",
        },
    },
    "ta": {
        "label": "Tamil",
        "unicode": re.compile(r"[\u0B80-\u0BFF]"),
        "romanized": {
            "illai", "irukku", "venum", "enna", "epdi", "romba", "seri",
            "enakku", "ungalukku", "nalla", "vendam", "eppo", "yaen",
            "solunga", "irukken", "pannunga",
        },
    },
    "kn": {
        "label": "Kannada",
        "unicode": re.compile(r"[\u0C80-\u0CFF]"),
        "romanized": {
            "illa", "beku", "hege", "yaake", "nanu", "swalpa", "aagide",
            "gottilla", "chennagide", "kelsa", "yavaga", "hodilla", "helu",
            "madi", "khali",
        },
    },
}

LANG_LABELS = {"en": "English", **{code: p["label"] for code, p in LANGUAGE_PROFILES.items()}}


def detect_language(text: str) -> dict:
    lower = text.lower()
    words = set(re.findall(r"[a-zA-Z]+", lower))
    has_latin_words = bool(re.search(r"[a-zA-Z]{3,}", text))

    # 1. native script present -> highest-confidence signal
    for code, profile in LANGUAGE_PROFILES.items():
        if profile["unicode"].search(text):
            if has_latin_words:
                return {
                    "language": f"{code}-en",
                    "label": f"{profile['label']}-English (code-mixed script)",
                    "is_code_mixed": True,
                }
            return {"language": code, "label": profile["label"], "is_code_mixed": False}

    # 2. romanized code-mixed check -- pick whichever language's marker
    # words show up most, so "signal ledu naa phone lo" -> Telugu, not Hindi
    best_code, best_hits = None, 0
    for code, profile in LANGUAGE_PROFILES.items():
        hits = len(words & profile["romanized"])
        if hits > best_hits:
            best_code, best_hits = code, hits

    if best_hits >= 2:
        profile = LANGUAGE_PROFILES[best_code]
        return {
            "language": f"{best_code}-en-latin",
            "label": f"{profile['label']}-English (romanized, code-mixed)",
            "is_code_mixed": True,
        }

    # 3. fall back to a general-purpose detector for plain English or any
    # native-script language typed without code-mixing
    try:
        code = detect(text)
    except LangDetectException:
        code = "en"

    label = LANG_LABELS.get(code, code)
    return {"language": code, "label": label, "is_code_mixed": False}


def _base_lang_code(detected_language: str) -> str:
    """'te-en' / 'te-en-latin' / 'te' all mean 'Telugu' as far as the
    translator is concerned -- strip down to the base ISO code."""
    return detected_language.split("-")[0]


def to_english(text: str, detected_language: str) -> str:
    """Best-effort translation to English for the NLU pipeline. Falls back
    to the original text (untranslated) if there's no internet access or
    the translator errors out -- the rest of the pipeline still runs on the
    romanized/code-mixed text, just with lower confidence."""
    if _base_lang_code(detected_language) == "en":
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return text


def from_english(text: str, target_language: str) -> str:
    base = _base_lang_code(target_language)
    if base == "en" or base not in LANGUAGE_PROFILES:
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target=base).translate(text)
    except Exception:
        return text
