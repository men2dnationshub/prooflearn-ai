"""ProofLearn AI application entry point and page router."""

import streamlit as st

from modules.config import APP_NAME

st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/1_Assignment_Review.py", title="Assignment Review", icon="📄"),
    st.Page("pages/2_Proof_of_Learning.py", title="Proof of Learning", icon="🎓"),
    st.Page("pages/3_Writing_Assistant.py", title="Writing Assistant", icon="✍️"),
    st.Page("pages/4_Dataset_Lab.py", title="Dataset Lab", icon="🧪"),
    st.Page("pages/5_Reports.py", title="Reports", icon="📊"),
]

st.navigation(pages).run()
