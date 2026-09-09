import streamlit as st
from modules.writing_assistant import assistance_declaration, improve_writing, writing_revision_json
from ui.shared import ReportItem, apply_brand, initialise_state, register_report, render_sidebar_status
initialise_state(); apply_brand(); render_sidebar_status(); st.title("Responsible Writing Assistant")
st.warning("This tool improves writing quality. It is not designed to bypass AI detection or conceal academic misconduct.")
active = st.session_state.get("active_document"); default_text = active.text if active else ""
text = st.text_area("Text to improve", value=default_text, height=280)
goals = st.multiselect("Writing goals", ["clarity", "conciseness", "grammar", "flow", "simplify", "professional", "academic"], default=["clarity", "grammar"])
if st.button("Create transparent revision", type="primary"):
    try: revision = improve_writing(text, goals)
    except ValueError as error: st.error(str(error))
    else:
        st.session_state["writing_revision"] = revision
        declaration = assistance_declaration(revision)
        register_report(ReportItem("writing_revision", "Writing revision", "writing_revision.json", "application/json", writing_revision_json(revision), "Writing"))
        register_report(ReportItem("revised_text", "Revised text", "revised_text.txt", "text/plain", revision.revised_text, "Writing"))
        register_report(ReportItem("ai_declaration", "AI assistance declaration", "ai_assistance_declaration.txt", "text/plain", declaration, "Writing"))
revision = st.session_state.get("writing_revision")
if revision:
    st.info(revision.review_notice)
    original, revised = st.columns(2)
    with original: st.markdown("#### Original"); st.text_area("Original text", revision.original_text, height=360, disabled=True)
    with revised: st.markdown("#### Suggested revision"); st.text_area("Revised text", revision.revised_text, height=360)
    cols = st.columns(3); cols[0].metric("Changes", len(revision.changes)); cols[1].metric("Words", revision.revised_word_count, revision.revised_word_count - revision.original_word_count); cols[2].metric("Reading ease", revision.revised_reading_ease, round(revision.revised_reading_ease - revision.original_reading_ease, 1))
    if revision.changes: st.dataframe([{"Goal": c.category.title(), "Original": c.original, "Suggestion": c.replacement, "Occurrences": c.occurrences, "Why": c.explanation} for c in revision.changes], hide_index=True, use_container_width=True)
    else: st.success("No supported rule-based changes were needed for the selected goals.")
    st.download_button("Download revised text", revision.revised_text, "revised_text.txt", "text/plain")
    st.download_button("Download AI assistance declaration", assistance_declaration(revision), "ai_assistance_declaration.txt", "text/plain")
