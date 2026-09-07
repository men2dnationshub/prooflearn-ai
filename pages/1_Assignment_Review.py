import json
import streamlit as st
from modules.authorship_model import predict_authorship
from modules.document_reader import DocumentExtractionError, extract_document
from modules.feature_extractor import analyse_writing
from modules.passage_analyzer import analyse_passages, passage_analysis_json
from modules.risk_engine import assess_review_risk, risk_assessment_json
from ui.shared import ReportItem, apply_brand, clear_document_workspace, initialise_state, register_report, render_sidebar_status

st.set_page_config(page_title="Assignment Review", page_icon="📄", layout="wide")
initialise_state(); apply_brand(); render_sidebar_status(); st.title("Assignment Review")
uploaded = st.file_uploader("Upload DOCX, PDF or TXT", type=["docx", "pdf", "txt"])
if uploaded:
    try: st.session_state["active_document"] = extract_document(uploaded.getvalue(), uploaded.name)
    except DocumentExtractionError as error: st.error(str(error))
document = st.session_state.get("active_document")
if not document: st.info("Upload an assignment to begin."); st.stop()
analysis = analyse_writing(document.text)
register_report(ReportItem("text", "Extracted text", f"{document.filename}_extracted.txt", "text/plain", document.text, "Assignment"))
register_report(ReportItem("analysis", "Writing analysis", f"{document.filename}_analysis.json", "application/json", json.dumps(analysis.to_dict(), indent=2), "Assignment"))
if st.button("Clear assignment"): clear_document_workspace(); st.rerun()
cols = st.columns(4); cols[0].metric("Words", document.word_count); cols[1].metric("Sentences", analysis.sentence_count); cols[2].metric("Paragraphs", document.paragraph_count); cols[3].metric("Reading ease", analysis.flesch_reading_ease)
text_tab, indicators_tab, passages_tab, review_tab = st.tabs(["Extracted text", "Writing indicators", "Passage analysis", "Authorship review"])
with text_tab: st.text_area("Text", document.text, height=420)
with indicators_tab:
    st.warning("These patterns are not proof of AI use.")
    for note in analysis.interpretation: st.write(f"• {note}")
    st.json(analysis.to_dict())
with passages_tab:
    try: report = analyse_passages(document.text)
    except ValueError as error: st.info(str(error))
    else:
        register_report(ReportItem("passages", "Passage analysis", f"{document.filename}_passages.json", "application/json", passage_analysis_json(report), "Assignment"))
        st.warning(report.disclaimer)
        st.dataframe([{"Passage": p.passage_id, "Reference": p.reference, "Words": p.word_count, "Variation": p.variation_level.replace("_", " ").title(), "Score": p.variation_score} for p in report.passages], hide_index=True, use_container_width=True)
with review_tab:
    if "baseline_model" not in st.session_state: st.info("Train an experimental model in Dataset Lab first.")
    else:
        try: prediction = predict_authorship(st.session_state["baseline_model"], document.text)
        except ValueError as error: st.info(str(error))
        else:
            risk = assess_review_risk(prediction, analysis, st.session_state["baseline_model"].evaluation)
            register_report(ReportItem("risk", "Authorship review", f"{document.filename}_review.json", "application/json", risk_assessment_json(risk), "Assignment")); st.error(risk.disclaimer)
            if risk.score is None:
                st.warning("Insufficient evidence. ProofLearn abstained from scoring.")
                for reason in risk.safeguards_triggered: st.write(f"• {reason}")
            else:
                rcols = st.columns(3); rcols[0].metric("Review level", risk.outcome.title()); rcols[1].metric("Score", f"{risk.score}/100"); rcols[2].metric("Evidence", risk.evidence_quality.title()); st.info(risk.recommended_action)
