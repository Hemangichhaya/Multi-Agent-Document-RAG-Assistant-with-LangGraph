# summary.py - Updated with better integration
import streamlit as st
import time
from datetime import datetime

def get_chat_model():
    """Get the chat model for summary generation"""
    import google.generativeai as genai
    api_key = st.session_state.get("api_key")
    
    if not api_key:
        st.error("❌ No API key found. Please add your Google Gemini API key in the sidebar.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model_name = st.session_state.get("model", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        st.error(f"❌ Error initializing chat model: {str(e)}")
        return None

def generate_document_summary_sync(doc_name: str, chat_model):
    """Generate summary for a specific document (synchronous version)"""
    try:
        if doc_name not in st.session_state.document_retrievers:
            return None
        
        retriever = st.session_state.document_retrievers[doc_name]
        
        sample_queries = [
            "main topics and key points",
            "important conclusions and findings", 
            "methodology and approach"
        ]
        
        all_chunks = []
        for query in sample_queries:
            try:
                chunks = retriever.invoke(query)
                all_chunks.extend(chunks[:2])
            except:
                continue
        
        # Remove duplicates
        unique_chunks = []
        seen_content = set()
        for chunk in all_chunks:
            if chunk.page_content[:100] not in seen_content:
                unique_chunks.append(chunk)
                seen_content.add(chunk.page_content[:100])
        
        content_parts = [chunk.page_content for chunk in unique_chunks[:8]]
        combined_content = "\n\n".join(content_parts)
        
        if len(combined_content) > 16000:
            combined_content = combined_content[:16000] + "\n... [Content truncated]"
        
        summary_prompt = f"""
        Please provide a comprehensive summary of this document: {doc_name}
        
        Content to summarize:
        {combined_content}
        
        Please provide a summary that includes:
        1. **Main Topic/Purpose**: What is this document about?
        2. **Key Points**: Most important points or findings (use bullet points)
        3. **Structure**: How is the content organized?
        4. **Important Details**: Notable data, dates, names, or statistics
        5. **Conclusions**: Main outcomes or recommendations (if any)
        
        Format your response with clear markdown headings and bullet points.
        Keep the summary concise but comprehensive (aim for 200-400 words).
        """
        
        response = chat_model.generate_content(summary_prompt)
        return response.text
        
    except Exception as e:
        st.error(f"Error generating summary for {doc_name}: {str(e)}")
        return None

def generate_summary_for_document(doc_name: str):
    """Generate summary for a document"""
    chat_model = get_chat_model()
    if not chat_model:
        st.error("❌ Could not initialize chat model for summary generation.")
        return
    
    # Mark as generating
    if 'summary_generating' not in st.session_state:
        st.session_state.summary_generating = set()
    st.session_state.summary_generating.add(doc_name)
    
    with st.spinner(f"🤖 Generating summary for {doc_name}..."):
        try:
            summary = generate_document_summary_sync(doc_name, chat_model)
            
            if summary:
                # Initialize document_summaries if not exists
                if 'document_summaries' not in st.session_state:
                    st.session_state.document_summaries = {}
                    
                st.session_state.document_summaries[doc_name] = {
                    'content': summary,
                    'generated_at': datetime.now().isoformat(),
                    'model': st.session_state.get('model', 'gemini-2.0-flash')
                }
                st.success(f"✅ Summary generated for {doc_name}!")
                
                # Set flags to show summary in chat
                st.session_state.show_summary_in_chat = True
                st.session_state.summary_doc_name = doc_name
            else:
                st.error(f"❌ Failed to generate summary for {doc_name}")
        except Exception as e:
            st.error(f"❌ Error generating summary: {str(e)}")
        finally:
            # Remove from generating set
            if 'summary_generating' in st.session_state:
                st.session_state.summary_generating.discard(doc_name)
    
    st.rerun()

def generate_all_summaries(doc_names):
    """Generate summaries for multiple documents"""
    chat_model = get_chat_model()
    if not chat_model:
        st.error("❌ Could not initialize chat model for summary generation.")
        return
    
    total_docs = len(doc_names)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    successful = 0
    failed = 0
    
    for i, doc_name in enumerate(doc_names):
        status_text.text(f"🤖 Generating summary {i+1}/{total_docs}: {doc_name}")
        
        # Mark as generating
        if 'summary_generating' not in st.session_state:
            st.session_state.summary_generating = set()
        st.session_state.summary_generating.add(doc_name)
        
        try:
            summary = generate_document_summary_sync(doc_name, chat_model)
            
            if summary:
                # Initialize document_summaries if not exists
                if 'document_summaries' not in st.session_state:
                    st.session_state.document_summaries = {}
                    
                st.session_state.document_summaries[doc_name] = {
                    'content': summary,
                    'generated_at': datetime.now().isoformat(),
                    'model': st.session_state.get('model', 'gemini-2.0-flash')
                }
                successful += 1
            else:
                failed += 1
        except Exception as e:
            st.error(f"❌ Error generating summary for {doc_name}: {str(e)}")
            failed += 1
        finally:
            # Remove from generating set
            if 'summary_generating' in st.session_state:
                st.session_state.summary_generating.discard(doc_name)
        
        progress_bar.progress((i + 1) / total_docs)
        
        # Add small delay between requests to avoid rate limiting
        if i < total_docs - 1:
            time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    if successful > 0:
        st.success(f"✅ Generated {successful} summaries successfully!")
    if failed > 0:
        st.warning(f"⚠️ Failed to generate {failed} summaries")
    
    st.rerun()

def display_document_summary(doc_name: str):
    """Display the summary for a document"""
    if 'document_summaries' not in st.session_state or doc_name not in st.session_state.document_summaries:
        return
    
    summary_data = st.session_state.document_summaries[doc_name]
    
    st.divider()
    st.subheader(f"📋 Summary: {doc_name}")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.info(f"Generated: {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')}")
    with col2:
        st.info(f"Model: {summary_data['model']}")
    with col3:
        if st.button("❌ Close", key="close_summary"):
            if hasattr(st.session_state, 'selected_summary'):
                delattr(st.session_state, 'selected_summary')
            st.rerun()
    
    # Display summary in a nice format
    with st.container():
        st.markdown(summary_data['content'])
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Regenerate", key="regenerate_summary"):
            generate_summary_for_document(doc_name)
    with col2:
        if st.button("📋 Copy", key="copy_summary"):
            st.code(summary_data['content'], language="markdown")
    with col3:
        # Download summary button
        summary_download = create_summary_download(doc_name, summary_data)
        st.download_button(
            label="⬇️ Download",
            data=summary_download,
            file_name=f"summary_{doc_name}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="download_summary"
        )

def create_summary_download(doc_name, summary_data):
    """Create downloadable content for document summary"""
    content = [
        f"# Document Summary: {doc_name}",
        f"",
        f"**Generated:** {datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')}",
        f"**Model:** {summary_data['model']}",
        f"",
        "---",
        f"",
        summary_data['content']
    ]
    
    return "\n".join(content)