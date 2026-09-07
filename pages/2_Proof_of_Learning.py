import streamlit as st
from modules.question_generator import generate_verification_questions, score_verification, verification_report_json
from ui.shared import ReportItem, apply_brand, initialise_state, register_report, render_sidebar_status

st.set_page_config(page_title="Proof of Learning", page_icon="🎓", layout="wide")
initialise_state(); apply_brand(); render_sidebar_status(); st.title("Proof of Learning")
document = st.session_state.get("active_document")
if not document: st.info("Upload an assignment on Assignment Review first."); st.stop()
try: bank = generate_verification_questions(document.text)
except ValueError as error: st.info(str(error)); st.stop()
st.warning(bank.disclaimer); options = {"Not assessed": None, "0 · Unable": 0, "1 · Partial": 1, "2 · Adequate": 2, "3 · Strong": 3}
with st.form("verification"):
    ratings = {}; notes = {}
    for q in bank.questions:
        st.markdown(f"#### {q.question_id} · {q.category.title()}"); st.write(q.question); st.caption(q.source_reference); st.info(q.source_excerpt)
        ratings[q.question_id] = options[st.selectbox("Rating", list(options), key=f"r_{bank.document_sha256}_{q.question_id}")]
        notes[q.question_id] = st.text_area("Evidence or notes", key=f"n_{bank.document_sha256}_{q.question_id}")
    submitted = st.form_submit_button("Calculate verification result", type="primary")
if submitted:
    result = score_verification(bank, ratings, notes); st.session_state["verification_result"] = result
    register_report(ReportItem("verification", "Learning verification", f"{document.filename}_verification.json", "application/json", verification_report_json(bank, result), "Verification"))
    if result.score is None: st.warning(result.interpretation)
    else: st.success(f"{result.score}/100 · {result.level.title()}. {result.interpretation}")
