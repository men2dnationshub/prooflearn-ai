import json
import pytest
from modules.writing_assistant import assistance_declaration, improve_writing, writing_revision_json

TEXT = "Due to the fact that the team team wanted to utilize data ,it collected a large number of records. It is important to note that the process has the ability to facilitate better decisions."

def test_transparent_revision_applies_selected_rules():
    result = improve_writing(TEXT, ["clarity", "conciseness", "grammar", "simplify"])
    assert "because" in result.revised_text.lower() and "team team" not in result.revised_text.lower()
    assert "use data" in result.revised_text.lower() and len(result.changes) >= 4

def test_unselected_tone_rule_is_not_applied():
    result = improve_writing("The review shows that a lot of people completed the detailed learning activity successfully.", ["grammar"])
    assert "shows that" in result.revised_text and "a lot of" in result.revised_text

def test_revision_is_deterministic_and_idempotent():
    first = improve_writing(TEXT, ["clarity", "grammar"])
    second = improve_writing(TEXT, ["clarity", "grammar"])
    assert first == second
    third = improve_writing(first.revised_text, ["clarity", "grammar"])
    assert third.revised_text == first.revised_text

def test_declaration_and_json_disclose_assistance():
    result = improve_writing(TEXT, ["clarity"])
    assert "AI assistance used: Yes" in assistance_declaration(result)
    data = json.loads(writing_revision_json(result))
    assert data["original_text"] == TEXT and data["review_notice"]

@pytest.mark.parametrize("goals", [[], ["bypass detector"], ["humanize"]])
def test_rejects_missing_or_unsupported_goals(goals):
    with pytest.raises(ValueError): improve_writing(TEXT, goals)

def test_rejects_too_short_text():
    with pytest.raises(ValueError, match="at least 10 words"): improve_writing("Too short.", ["clarity"])
