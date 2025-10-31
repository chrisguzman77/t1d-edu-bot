# app/safety/rules.py

from __future__ import annotations
from dataclasses import dataclass
import re
import string

# Categories we want to block or redirect
BLOCK_KEYWORDS = {
    "dosing": [
        "dose", "dosing", "bolus", "basal", "units of insulin", "how many units",
        "increase my insulin", "lower my insulin", "titrate", "carb ratio",
        "correction factor", "isf", "ic ratio", "pump settings"
    ],
    "diagnosis": [
        "do i have diabetes", "do i have type 1", "diagnose", "is this diabetes",
        "should i start insulin", "am i diabetic"
    ],
    "urgent": [
        "seizure", "unconscious", "not breathing", "trouble breathing", "dka",
        "ketones and vomiting", "confused and sweating a lot"
    ],
}

# Common misspelings / variants you saw in logs (keep growing this list)
ALIASES = {
    "bolus": ["bolis", "bolous", "boslus"],
    "basal": ["basel", "basual"]
}

# Regex for "N units" style questions, e.g., "take 2 units?", "give 5u?"
RE_UNITS = re.compile(r"\b(\d{1,2})\s*(u|units|unit)\b", re.I)
# Regex for explicit number + "carbs" (indicates dosing intent with ratios)
RE_CARBS = re.compile(r"\b(\d{1,3})\s*(g|grams)\s*carb(s)?\b", re.I)

@dataclass(frozen=True)
class SafetyResult:
    blocked: bool           # True = refuse and do not call LLM
    category: str | None    # "dosing" | "diagnosis" | "urgent" | None
    reason: str | None      # short internal reason
    message: str | None     # end-user safe response

DISCLAIMER = (
    "Disclaimer: Educational info only. No medical advice or dosing."
    "For personal care, contact your clinician. Emergencies: call local services."
)

REFUSALS = {
    "dosing": (
        f"{DISCLAIMER}\n\n"
        "I can’t help with insulin dosing, pump settings, or carb ratios. "
        "Please contact your diabetes care team for personalized guidance."
    ),
    "diagnosis": (
        f"{DISCLAIMER}\n\n"
        "I can’t diagnose. If you’re concerned about Type 1 diabetes or any symptoms, "
        "please see a healthcare professional for testing and evaluation."
    ),
    "urgent": (
        f"{DISCLAIMER}\n\n"
        "This sounds urgent. Please seek immediate medical attention or call emergency services."
    ),
}

def _normalize(text: str) -> str:
    t = text.lower()
    # expand known aliases
    for base, alts in ALIASES.items():
        for alt in alts:
            t = t.replace(alt, base)
    # lightweight punctuation removal to help keyword matching
    table = str.maketrans("","", string.punctuation.replace("-", ""))
    return t.translate(table)

def _hit_keywords(t: str) -> str | None:
    """Return category name if any category keywords appear."""
    for cat, words in BLOCK_KEYWORDS.items():
        for w in words:
            if w in t:
                return cat
    return None

def safety_check(user_text: str) -> SafetyResult:
    """
    Returns SafetyResult. If blocked=True, do NOt call the LLM.
    """
    if not user_text or not user_text.strip():
        return SafetyResult(False, None, None, None)
    
    t = _normalize(user_text)

    # 1) direct keyword block
    cat = _hit_keywords(t)
    if cat:
        return SafetyResult(True, cat, f"matched keyword in {cat}", REFUSALS[cat])
    
    #2) patterns implying dosing intent (numbers + units, carbs)
    if RE_UNITS.search(t) or RE_CARBS.search(t):
        return SafetyResult(True, "dosing", "regex units/carbs", REFUSALS["dosing"])
    
    #3) heuristics for "change my dose", "adjust insulin", etc.
    if ("change" in t or "adjust" in t or "increase" in t or "decrease" in t) and "insulin" in t:
        return SafetyResult(True, "dosing", "adjust insulin heuristic", REFUSALS["dosing"])
    
    #4) crisis heuristics (compound phrases)
    if ("very low" in t and "confused" in t) or ("passed out" in t):
        return SafetyResult(True, "urgent", "crisis heuristic", REFUSALS["urgent"])
    
    return SafetyResult(False, None, None, None)