"""ProofLearn AI home dashboard."""

import streamlit as st

from modules.config import APP_NAME, APP_TAGLINE, APP_VERSION
from ui.shared import apply_brand, initialise_state, render_sidebar_status

initialise_state()
apply_brand()
render_sidebar_status()

st.title(APP_NAME)
st.caption(APP_TAGLINE)
st.info("Detection identifies review risk. Student verification establishes evidence of learning.")
st.markdown("### Start a review")

for column, item in zip(
    st.columns(3),
    [
        ("📄", "Assignment Review", "Upload a document or try the safe sample assignment."),
        ("🎓", "Proof of Learning", "Generate questions that help a student demonstrate understanding."),
        ("📊", "Reports", "Review and download the evidence produced during this session."),
    ],
):
    with column:
        with st.container(border=True):
            st.markdown(f"### {item[0]} {item[1]}")
            st.write(item[2])

metrics = st.columns(3)
metrics[0].metric("Active assignment", "Ready" if st.session_state.get("active_document") else "Not uploaded")
metrics[1].metric("Experimental model", "Ready" if "baseline_model" in st.session_state else "Not trained")
metrics[2].metric("Available reports", len(st.session_state["report_registry"]))

with st.expander("Before you use ProofLearn AI"):
    st.write("Use synthetic, public or properly authorised documents during prototype testing.")
    st.write("Remove names, registration numbers and other identifying information where possible.")
    st.write("Never use a score or writing pattern alone to accuse, grade or penalise a student.")

st.warning("ProofLearn AI is a controlled prototype. Its outputs require human review and student verification.")
st.caption(f"{APP_NAME} v{APP_VERSION} · Deployable prototype · Not production validated")
