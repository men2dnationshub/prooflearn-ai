import streamlit as st
from modules.config import APP_NAME, APP_TAGLINE, APP_VERSION
from ui.shared import apply_brand, initialise_state, render_sidebar_status

st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")
initialise_state(); apply_brand(); render_sidebar_status()
st.title(APP_NAME); st.caption(APP_TAGLINE)
st.info("Detection identifies review risk. Student verification establishes evidence of learning.")
st.markdown("### Review workflow")
for column, item in zip(st.columns(3), [("1", "Assignment Review", "Upload and inspect writing."), ("2", "Proof of Learning", "Verify student understanding."), ("3", "Reports", "Download review evidence.")]):
    with column: st.markdown(f"#### {item[0]}. {item[1]}"); st.write(item[2])
metrics = st.columns(3)
metrics[0].metric("Active assignment", "Ready" if st.session_state.get("active_document") else "Not uploaded")
metrics[1].metric("Experimental model", "Ready" if "baseline_model" in st.session_state else "Not trained")
metrics[2].metric("Available reports", len(st.session_state["report_registry"]))
st.warning("No score or writing pattern should be used alone to accuse or penalise a student.")
st.caption(f"{APP_NAME} v{APP_VERSION} · Deployable prototype · Not production validated")
