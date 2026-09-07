from io import BytesIO
from docx import Document
from modules.document_reader import extract_document
from modules.feature_extractor import analyse_writing
from modules.passage_analyzer import analyse_passages
from modules.question_generator import generate_verification_questions, score_verification

def _assignment_bytes():
    stream = BytesIO(); document = Document()
    for number in range(3):
        document.add_paragraph(" ".join(f"Classroom analysis sentence {index} explains evidence, method and learning outcome {number}." for index in range(10)))
    document.save(stream); return stream.getvalue()

def test_document_to_learning_verification_workflow():
    document = extract_document(_assignment_bytes(), "assignment.docx")
    analysis = analyse_writing(document.text)
    passages = analyse_passages(document.text)
    bank = generate_verification_questions(document.text)
    result = score_verification(bank, {question.question_id: 2 for question in bank.questions})
    assert document.word_count == analysis.word_count
    assert passages.passage_count >= 2
    assert result.score == 66.7 and result.level == "ADEQUATE"

def test_short_text_fails_safely_at_later_stages():
    document = extract_document(b"A short but readable assignment.", "short.txt")
    assert analyse_writing(document.text).word_count == 5
    try: analyse_passages(document.text)
    except ValueError as error: assert "at least" in str(error)
    else: raise AssertionError("Passage analysis should abstain")
