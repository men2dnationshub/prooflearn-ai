from dataclasses import dataclass
import streamlit as st
from modules.config import APP_NAME, APP_VERSION

@dataclass(frozen=True)
class ReportItem:
    report_id: str
    title: str
    filename: str
    mime: str
    data: str | bytes
    category: str

def initialise_state():
    st.session_state.setdefault("report_registry", {})

def register_report(item):
    initialise_state(); st.session_state["report_registry"][item.report_id] = item

def clear_document_workspace():
    st.session_state.pop("active_document", None)
    st.session_state["report_registry"] = {k: v for k, v in st.session_state.get("report_registry", {}).items() if v.category == "Model"}

def apply_brand():
    st.markdown('<style>.stApp{color:#061A40}[data-testid="stSidebar"]{background:#F2F6FC;border-right:1px solid #D8E4F3}[data-testid="stMetric"]{border:1px solid #D8E4F3;border-radius:12px;padding:12px}h1,h2,h3{color:#061A40}.stButton>button{border-radius:9px;font-weight:600}</style>', unsafe_allow_html=True)

def render_sidebar_status():
    initialise_state()
    with st.sidebar:
        st.markdown(f"### 🎓 {APP_NAME}"); st.caption("Verify Authorship · Validate Learning"); st.caption(f"Version {APP_VERSION}"); st.divider()
        st.write("✅ Assignment loaded" if "active_document" in st.session_state else "○ Assignment not loaded")
        st.write("✅ Model trained" if "baseline_model" in st.session_state else "○ Model not trained")
        st.write(f"📄 {len(st.session_state['report_registry'])} report(s) ready")
        st.divider()
        st.caption("Prototype only · Human review required")
