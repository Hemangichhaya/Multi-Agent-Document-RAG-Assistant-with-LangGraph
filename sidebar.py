# sidebar.py - Fixed to track chat_history instead of messages
import streamlit as st
import os
from config import DEFAULT_SYSTEM_MESSAGE, EMBEDDING_MODEL_OPTIONS
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
import gc

def setup_sidebar():
    st.sidebar.header("🔑 Configuration")

    api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        st.sidebar.success("✅ API key configured")
    else:
        st.sidebar.info("💡 Enter your API key to start")

    st.sidebar.subheader("🧠 Embedding Model")
    selected_embedding = st.sidebar.selectbox(
        "Choose Model (Free)", list(EMBEDDING_MODEL_OPTIONS.keys())
    )
    st.session_state.embedding_model = selected_embedding

    st.sidebar.subheader("🤖 Generation Model")
    selected_model = st.sidebar.selectbox(
        "Choose Gemini Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    )
    st.session_state.model = selected_model

    st.sidebar.divider()

    # Session Info - FIXED to use chat_history
    st.sidebar.subheader("📊 Session Info")
    
    # Initialize chat_history if it doesn't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Get counts from the correct session state variables
    message_count = len(st.session_state.chat_history)
    document_count = len(st.session_state.get('processed_documents', {}))
    summary_count = len(st.session_state.get('document_summaries', {}))
    
    # # Get selected documents count
    # selected_docs_count = 0
    # if 'selected_docs' in st.session_state:
    #     selected_docs_count = len(st.session_state.selected_docs)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Conversations", message_count)
        st.metric("Summaries", summary_count)
    with col2:
        st.metric("Documents", document_count)
        # st.metric("Selected", selected_docs_count)

    if document_count > 0:
        processed_docs = st.session_state.get('processed_documents', {})
        total_chunks = sum(doc.get('chunks', 0) for doc in processed_docs.values())
        st.sidebar.success(f"📄 {document_count} document(s) ready ({total_chunks} chunks)")
        
        # # Show selected documents
        # if selected_docs_count > 0:
        #     selected_docs = st.session_state.get('selected_docs', [])
        #     if selected_docs_count == 1:
        #         st.sidebar.info(f"📋 Active: {selected_docs[0]}")
        #     else:
        #         st.sidebar.info(f"📋 Active: {selected_docs_count} documents")
        # else:
        #     st.sidebar.warning("⚠️ No documents selected")
    else:
        st.sidebar.info("📄 No documents processed yet")

    # Add multi-agent status in sidebar
    st.sidebar.divider()
    st.sidebar.subheader("🤖 Multi-Agent System")
    
    multi_agent_status = st.sidebar.checkbox(
        "Enable Multi-Agent System", 
        value=st.session_state.get("multi_agent_enabled", True),
        help="Use multiple specialized AI agents for enhanced responses"
    )
    st.session_state.multi_agent_enabled = multi_agent_status
    
    if multi_agent_status:
        st.sidebar.success("✅ Multi-Agent: Active")
        with st.sidebar.expander("🔍 Agent Details", expanded=False):
            st.markdown("""
            **Active Agents:**
            - 🕵️ Document Retriever
            - 📝 Content Summarizer
            - 🔍 Document Analyst
            - ✨ Quality Assurance
            
            **Tools Available:** 5
            **Workflow:** Enhanced
            """)
    else:
        st.sidebar.warning("⚠️ Multi-Agent: Disabled")

    # Show recent activity
    if message_count > 0:
        st.sidebar.divider()
        st.sidebar.subheader("📝 Recent Activity")
        
        # Show last 3 queries
        recent_chats = st.session_state.chat_history[-3:]
        for i, chat in enumerate(reversed(recent_chats)):
            query_preview = chat.get('query', 'Unknown query')
            if len(query_preview) > 40:
                query_preview = query_preview[:37] + "..."
            
            agent_icon = "🤖" if chat.get('agent_generated') else "🔧"
            doc_name = chat.get('document', 'Unknown')
            if isinstance(doc_name, str) and len(doc_name) > 20:
                doc_name = doc_name[:17] + "..."
            
            st.sidebar.text(f"{agent_icon} {query_preview}")
            st.sidebar.caption(f"📄 {doc_name}")
            
            if i < len(recent_chats) - 1:
                st.sidebar.markdown("---")

    # Controls
    st.sidebar.divider()
    st.sidebar.subheader("🎛️ Controls")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear chat history only"):
            clear_chat_only()
            st.rerun()
    
    with col2:
        if st.button("🔄 Clear All", use_container_width=True, help="Clear everything including documents"):
            clear_all_data()
            st.rerun()
    
    # Add export button
    if message_count > 0:
        st.sidebar.divider()
        if st.sidebar.button("📤 Quick Export JSON", use_container_width=True):
            export_sidebar_quick()

    return selected_model, api_key


def clear_chat_only():
    """Clear only chat history, keep documents"""
    st.session_state.chat_history = []
    
    # Also clear old messages format if it exists
    if 'messages' in st.session_state:
        st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
    
    st.success("🗑️ Chat history cleared!")


def clear_all_data():
    """Clear all documents and chat with memory cleanup"""
    # Clear chat history
    st.session_state.chat_history = []
    
    # Clear documents
    st.session_state.processed_documents = {}
    st.session_state.document_retrievers = {}
    st.session_state.document_vector_stores = {}
    st.session_state.document_summaries = {}
    st.session_state.summary_generating = set()
    st.session_state.combined_retriever = None
    
    # Clear selections
    st.session_state.selected_docs = []
    st.session_state.selected_document = "All Documents"
    st.session_state.selected_documents = []
    
    # Clear old format if exists
    if "retriever" in st.session_state:
        del st.session_state["retriever"]
    if 'messages' in st.session_state:
        st.session_state.messages = [SystemMessage(content=DEFAULT_SYSTEM_MESSAGE)]
    
    st.session_state.chat_mode = "multi"
    
    # Force garbage collection
    gc.collect()
    st.success("🔄 All data cleared and memory freed!")


def export_sidebar_quick():
    """Quick export from sidebar"""
    import json
    from datetime import datetime
    
    if not st.session_state.get("chat_history"):
        st.sidebar.warning("No chat history to export.")
        return
    
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_conversations": len(st.session_state.chat_history),
        "documents_count": len(st.session_state.get('processed_documents', {})),
        "selected_documents": st.session_state.get('selected_docs', []),
        "multi_agent_enabled": st.session_state.get('multi_agent_enabled', True),
        "chat_history": st.session_state.chat_history
    }
    
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.sidebar.download_button(
        label="⬇️ Download Chat History",
        data=json_str,
        file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key="sidebar_quick_export"
    )