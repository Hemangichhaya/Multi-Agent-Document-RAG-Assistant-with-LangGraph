# app.py - Ensure you're importing from the right place
import streamlit as st
from state import init_session_state
from sidebar import setup_sidebar
from ui import document_upload_tab, summary_tab
from chat import chat_tab  # This now uses the enhanced chat_tab

def main():
    init_session_state()
    st.set_page_config(page_title="Advanced Multi-Agent Document RAG", page_icon="🤖", layout="wide")
    st.title("🤖 Advanced Multi-Agent Document RAG Assistant")
    selected_model, api_key = setup_sidebar()
    tab1, tab2, tab3 = st.tabs(["📁 Upload", "💬 Multi-Agent Chat", "📋 Summaries"])
    with tab1: 
        document_upload_tab()
    with tab2: 
        chat_tab()  # This now uses the enhanced multi-agent chat
    with tab3: 
        summary_tab()

if __name__ == "__main__":
    main()