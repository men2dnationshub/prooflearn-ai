"""Transparent, rule-based writing improvements with change disclosure."""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import re
from typing import Any
from modules.config import APP_VERSION
from modules.feature_extractor import analyse_writing

SUPPORTED_GOALS = {"clarity", "conciseness", "grammar", "flow", "simplify", "professional", "academic"}
RULES = {
    "clarity": (("due to the fact that", "because"), ("in order to", "to"), ("at this point in time", "now"), ("has the ability to", "can"), ("with regard to", "about")),
    "conciseness": (("a large number of", "many"), ("in the event that", "if"), ("for the purpose of", "to"), ("it is important to note that", "")),
    "simplify": (("utilization", "use"), ("utilize", "use"), ("commence", "start"), ("facilitate", "help"), ("approximately", "about"), ("numerous", "many"), ("sufficient", "enough")),
    "professional": (("a lot of", "many"), ("can't", "cannot"), ("won't", "will not"), ("don't", "do not"), ("doesn't", "does not")),
    "academic": (("shows that", "indicates that"), ("a big", "a substantial"), ("looked at", "examined")),
}

@dataclass(frozen=True)
class WritingChange:
    category: str
    original: str
    replacement: str
    explanation: str
    occurrences: int

@dataclass(frozen=True)
class WritingRevision:
    original_text: str
    revised_text: str
    goals: tuple[str, ...]
    changes: tuple[WritingChange, ...]
    original_word_count: int
    revised_word_count: int
    original_reading_ease: float
    revised_reading_ease: float
    disclosure: str
    review_notice: str

    def to_dict(self) -> dict[str, Any]: return asdict(self)

def _case_replacement(match: re.Match[str], replacement: str) -> str:
    if not replacement: return ""
    value = replacement
    if match.group(0)[:1].isupper(): value = value[:1].upper() + value[1:]
    return value

def _apply_phrase(text: str, original: str, replacement: str) -> tuple[str, int]:
    pattern = re.compile(rf"\b{re.escape(original)}\b", re.IGNORECASE)
    return pattern.subn(lambda match: _case_replacement(match, replacement), text)

def improve_writing(text: str, goals: list[str] | tuple[str, ...]) -> WritingRevision:
    if len(re.findall(r"\b\w+\b", str(text))) < 10: raise ValueError("Writing improvement requires at least 10 words.")
    if len(str(text).split()) > 10_000: raise ValueError("Writing improvement is limited to 10,000 words per request.")
    selected = tuple(dict.fromkeys(str(goal).strip().lower() for goal in goals))
    invalid = set(selected) - SUPPORTED_GOALS
    if invalid: raise ValueError("Unsupported writing goals: " + ", ".join(sorted(invalid)))
    if not selected: raise ValueError("Select at least one writing goal.")

    revised = str(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    changes = []
    if "grammar" in selected or "flow" in selected:
        cleaned, count = re.subn(r"\b([A-Za-z]+)\s+\1\b", r"\1", revised, flags=re.IGNORECASE)
        if count: changes.append(WritingChange("grammar", "Repeated consecutive word", "Single word", "Removed accidental word repetition.", count))
        revised = cleaned
        cleaned, count = re.subn(r"\s+([,.;:!?])", r"\1", revised)
        if count: changes.append(WritingChange("grammar", "Space before punctuation", "Correct punctuation spacing", "Corrected punctuation spacing.", count))
        revised = cleaned
        cleaned, count = re.subn(r"([,.;:!?])(?=[A-Za-z])", r"\1 ", revised)
        if count: changes.append(WritingChange("flow", "Missing space after punctuation", "Added space", "Improved sentence readability.", count))
        revised = cleaned
        cleaned = re.sub(r"[ \t]{2,}", " ", revised)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        if cleaned != revised: changes.append(WritingChange("flow", "Irregular spacing", "Consistent spacing", "Normalised spacing while preserving paragraphs.", 1))
        revised = cleaned

    applied = set()
    for goal in selected:
        for original, replacement in RULES.get(goal, ()):
            if original in applied: continue
            revised, count = _apply_phrase(revised, original, replacement)
            if count:
                changes.append(WritingChange(goal, original, replacement or "Removed", f"Applied the selected {goal} goal.", count))
                applied.add(original)

    original_analysis = analyse_writing(str(text))
    revised_analysis = analyse_writing(revised)
    return WritingRevision(
        original_text=str(text), revised_text=revised, goals=selected, changes=tuple(changes),
        original_word_count=original_analysis.word_count, revised_word_count=revised_analysis.word_count,
        original_reading_ease=original_analysis.flesch_reading_ease, revised_reading_ease=revised_analysis.flesch_reading_ease,
        disclosure=f"Edited with ProofLearn AI Writing Assistant v{APP_VERSION}. Goals: {', '.join(selected)}.",
        review_notice="Review every suggestion for accuracy, voice, citations and meaning before use. The user remains responsible for the final text.",
    )

def assistance_declaration(revision: WritingRevision) -> str:
    return ("AI ASSISTANCE DECLARATION\n\nAI assistance used: Yes\nTool: ProofLearn AI Writing Assistant "
            f"v{APP_VERSION}\nPurposes: {', '.join(revision.goals)}\n\nI reviewed the suggestions and accept responsibility for the final content.")

def writing_revision_json(revision: WritingRevision) -> str:
    return json.dumps(revision.to_dict(), indent=2, ensure_ascii=False)
