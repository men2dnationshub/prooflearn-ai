import streamlit as st
from ui.shared import apply_brand, initialise_state, render_sidebar_status
st.set_page_config(page_title="Reports", page_icon="📊", layout="wide")
initialise_state(); apply_brand(); render_sidebar_status(); st.title("Reports")
reports = st.session_state["report_registry"]
if not reports: st.info("No reports are available yet.")
else:
    categories = sorted({item.category for item in reports.values()}); selected = st.selectbox("Category", ["All", *categories])
    for item in [r for r in reports.values() if selected == "All" or r.category == selected]:
        with st.container(border=True): st.markdown(f"#### {item.title}"); st.caption(item.category); st.download_button("Download", item.data, item.filename, item.mime, key=item.report_id)
