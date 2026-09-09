from io import BytesIO
import pandas as pd
import streamlit as st
from modules.authorship_model import ModelTrainingError, evaluation_json, train_baseline
from modules.dataset_manager import empty_dataset_template, validate_dataset
from ui.shared import ReportItem, apply_brand, initialise_state, register_report, render_sidebar_status
initialise_state(); apply_brand(); render_sidebar_status(); st.title("Dataset Lab")
buffer = BytesIO(); empty_dataset_template().to_csv(buffer, index=False); st.download_button("Download dataset template", buffer.getvalue(), "prooflearn_training_template.csv", "text/csv")
uploaded = st.file_uploader("Upload authorised training CSV", type=["csv"])
if uploaded:
    try: data = pd.read_csv(uploaded)
    except Exception: st.error("The CSV could not be read.")
    else:
        report = validate_dataset(data); st.success("Dataset validation passed.") if report.is_valid else st.error("Dataset is not ready.")
        for item in report.errors: st.write(f"❌ {item}")
        for item in report.warnings: st.write(f"⚠️ {item}")
        if report.is_valid and st.button("Train baseline", type="primary"):
            try: bundle = train_baseline(data)
            except ModelTrainingError as error: st.error(str(error))
            else:
                st.session_state["baseline_model"] = bundle; register_report(ReportItem("model", "Model evaluation", "model_evaluation.json", "application/json", evaluation_json(bundle), "Model")); st.success("Experimental session model trained.")
