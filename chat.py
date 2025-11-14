# chat.py - Fixed version with working buttons and multi-document support
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from agents import get_multiagent_system

def chat_tab():
    """Chat tab for document-only multi-agent RAG system"""
    # Header
    st.markdown("# Multi-Agent Document RAG Chat")
    st.caption("Interact intelligently with your uploaded documents using specialized AI agents.")
    st.markdown("---")

    # # Section 0: Setup
    # st.markdown("## ⚙️ 0) Setup & Context")
    # st.info("This section initializes the multi-agent system. Make sure your API key and document retriever are loaded.")

    api_key = st.session_state.get("api_key")

    # Check API key
    if not api_key:
        st.warning(" Please add your Google Gemini API key in the sidebar before chatting.")
        return

    # Enhanced Document Selection and Info Section
    # st.markdown("---")
    st.markdown("## 1) Select Documents & Ask Your Question")

    # Document selection for chat
    processed_docs = st.session_state.get("processed_documents", {})
    if not processed_docs:
        st.warning("Please upload and process documents first in the Upload tab.")
        return
    
    doc_options = list(processed_docs.keys())
    
    # MULTI-SELECT: Allow selecting multiple documents
    st.markdown("### Select Documents to Chat With")
    
    # Initialize selected_docs in session state if not exists
    if 'selected_docs' not in st.session_state:
        st.session_state.selected_docs = []
    
    # Initialize a key for forcing multiselect refresh
    if 'multiselect_key' not in st.session_state:
        st.session_state.multiselect_key = 0
    
    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col2:
        # Quick selection buttons BEFORE multiselect
        st.markdown("**Quick Select:**")
        quick_col1, quick_col2 = st.columns(2)
        with quick_col1:
            if st.button("Select All", use_container_width=True, key="select_all_btn"):
                st.session_state.selected_docs = doc_options.copy()
                st.session_state.multiselect_key += 1  # Force multiselect to refresh
                st.rerun()
        with quick_col2:
            if st.button("Clear All", use_container_width=True, key="clear_all_btn"):
                st.session_state.selected_docs = []
                st.session_state.multiselect_key += 1  # Force multiselect to refresh
                st.rerun()
    
    with col1:
        # Ensure default values are in options
        valid_defaults = [doc for doc in st.session_state.selected_docs if doc in doc_options]
        
        # Use dynamic key to force widget recreation
        selected_docs = st.multiselect(
            "Choose one or more documents:",
            options=doc_options,
            default=valid_defaults,
            key=f"multi_doc_selector_{st.session_state.multiselect_key}"
        )
        
        # Update session state with current selection
        st.session_state.selected_docs = selected_docs
    
    # Handle document selection logic
    if not selected_docs:
        st.info("Please select at least one document to chat with")
        st.session_state.selected_documents = []
        st.session_state.current_retriever = None
        return
    elif len(selected_docs) == 1:
        # Single document mode
        st.session_state.selected_document = selected_docs[0]
        st.session_state.selected_documents = selected_docs
        current_retriever = st.session_state.document_retrievers.get(selected_docs[0])
        
        if not current_retriever:
            st.error(f"No retriever available for {selected_docs[0]}")
            st.info("Please go to the Upload tab and reprocess the documents.")
            return
        
        doc_info = processed_docs[selected_docs[0]]
        has_summary = selected_docs[0] in st.session_state.get('document_summaries', {})
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.info(f"**Single Document Mode:** {selected_docs[0]} ({doc_info['chunks']} chunks)")
        with col2:
            summary_status = "Has summary" if has_summary else "No summary yet"
            st.write(summary_status)
        with col3:
            if has_summary:
                if st.button("View Summary", key="view_summary_btn"):
                    st.session_state.show_summary_in_chat = True
                    st.session_state.summary_doc_name = selected_docs[0]
                    st.rerun()
            else:
                if st.button("Generate", key="generate_summary_btn"):
                    from summary import generate_summary_for_document
                    generate_summary_for_document(selected_docs[0])
        
        # Display summary if requested
        if st.session_state.get('show_summary_in_chat') and st.session_state.get('summary_doc_name') == selected_docs[0]:
            display_summary_in_chat(selected_docs[0])
        
        st.session_state.current_retriever = current_retriever
        st.success("Single document retriever ready")
    else:
        # Multi-document mode (2 or more documents)
        st.session_state.selected_document = "Multiple Documents"
        st.session_state.selected_documents = selected_docs
        st.session_state.current_retriever = "multi_document"  # Flag for multi-document processing
        
        st.info(f" **Multi-Document Mode:** {len(selected_docs)} documents selected")
        
        # Verify all selected documents have retrievers
        missing_retrievers = []
        for doc_name in selected_docs:
            if doc_name not in st.session_state.document_retrievers:
                missing_retrievers.append(doc_name)
        
        if missing_retrievers:
            st.error(f" Missing retrievers for: {', '.join(missing_retrievers)}")
            st.info("Please go to the Upload tab and reprocess the documents.")
            return
        
        # Show selected documents
        with st.expander("Selected Documents", expanded=True):
            for doc_name in selected_docs:
                doc_info = processed_docs[doc_name]
                st.write(f"• {doc_name} ({doc_info['chunks']} chunks)")
        
        st.success(f"All {len(selected_docs)} documents have retrievers ready")
    
    # Show agent and tool information
    with st.expander("Agent & Tool Configuration", expanded=False):
        st.markdown("""
        **Multi-Agent System Active:**
        - Document Retriever Agent
        - Content Summarizer Agent  
        - Document Analyst Agent
        - Quality Assurance Agent
        
        **Tools Available:**
        - Document Retrieval Tool
        - Text Summarization Tool
        - Content Analysis Tool
        - Citation Management Tool
        - Content Formatting Tool
        
        **Focus:** Document-only processing (no web search)
        """)
    
    st.markdown("---")

    # Suggested questions
    st.markdown("### Suggested Questions")
    suggested_questions = [
        "What is the main topic of this document?",
        "Explain the key concepts and ideas in detail",
        "Summarize the most important points comprehensively",
        "What are the main findings or conclusions?",
        "Describe the methodology or approach used",
        "Analyze the patterns and relationships in the content"
    ]
    
    # Create columns for suggested questions
    cols = st.columns(3)
    
    for i, question in enumerate(suggested_questions):
        with cols[i % 3]:
            button_key = f"suggested_{i}"
            if st.button(question, key=button_key, use_container_width=True):
                st.session_state.auto_query = question
                st.session_state.auto_process = True
                st.rerun()
    
    # Check if we should auto-process from session state
    auto_process = st.session_state.get("auto_process", False)
    auto_query = st.session_state.get("auto_query", "")
    
    # Query input
    query = st.text_input(
        "Enter your query:",
        placeholder="Ask me anything about your documents...",
        value=auto_query if auto_process else "",
        key="query_input"
    )
    
    # Determine if we should process
    should_process = False
    current_query = ""
    
    if auto_process and auto_query:
        should_process = True
        current_query = auto_query
        st.session_state.auto_process = False
        if "auto_query" in st.session_state:
            del st.session_state.auto_query
    elif query and not auto_process:
        should_process = True
        current_query = query

    # Section 2: Multi-Agent Workflow
    if should_process and current_query:
        st.markdown("---")
        st.markdown("## 2) Multi-Agent Workflow Execution")
        
        # Show which question is being processed
        if auto_query and current_query == auto_query:
            st.info(f"**Processing suggested question:** *{current_query}*")
        else:
            st.info(f"**Processing your question:** *{current_query}*")
        
        # Show agent workflow visualization
        with st.expander("Agent Workflow Progress", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info("Retrieval")
            with col2:
                st.info("Summarization")
            with col3:
                st.info("Analysis")
            with col4:
                st.info("Synthesis")
        
        # Handle multi-document vs single document processing
        if st.session_state.current_retriever == "multi_document":
            # Multi-document processing
            process_multi_document_query(current_query, st.session_state.selected_documents, api_key)
        else:
            # Single document processing
            process_single_document_query(current_query, api_key, st.session_state.current_retriever)

        # Export section
        st.markdown("---")
        st.markdown("## Export Chat")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export as JSON", use_container_width=True, key="export_json"):
                export_chat_as_json()
        with col2:
            if st.button("Export as Markdown", use_container_width=True, key="export_md"):
                export_chat_as_markdown()

    # Show chat history
    display_chat_history()

def process_multi_document_query(query, selected_docs, api_key):
    """Process query across multiple documents with separate sections for each"""
    st.markdown("### Processing Across Multiple Documents")
    
    # Create tabs for each document
    tabs = st.tabs([f"{doc}" for doc in selected_docs])
    
    all_responses = {}
    
    for i, (doc_name, tab) in enumerate(zip(selected_docs, tabs)):
        with tab:
            st.markdown(f"#### Analyzing: **{doc_name}**")
            
            # Get the retriever for this specific document
            retriever = st.session_state.document_retrievers.get(doc_name)
            
            if not retriever:
                st.error(f"No retriever available for {doc_name}")
                continue
            
            try:
                # Use the enhanced multi-agent system for each document
                with st.spinner(f"Analyzing {doc_name}..."):
                    crew = get_multiagent_system(api_key, retriever, use_enhanced=True)
                
                # Execute the multi-agent workflow for this document
                with st.spinner(f"Processing {doc_name}..."):
                    result = crew.kickoff(inputs={"query": query})
                
                # Display the result for this document
                st.markdown("##### Document-Specific Answer")
                st.write(result)
                
                # Store the response
                all_responses[doc_name] = result
                
                # Show source information for this document
                try:
                    source_docs = None
                    if hasattr(retriever, 'invoke'):
                        source_docs = retriever.invoke(query)
                    elif hasattr(retriever, 'get_relevant_documents'):
                        source_docs = retriever.get_relevant_documents(query)
                    elif callable(retriever):
                        source_docs = retriever(query)
                        
                    if source_docs:
                        with st.expander(f"Sources from {doc_name}", expanded=False):
                            for j, doc in enumerate(source_docs[:3]):
                                source_file = doc.metadata.get('source_file', 'Unknown')
                                st.markdown(f"**Source {j+1}:**")
                                st.text(f"{doc.page_content[:250]}...")
                                st.markdown("---")
                except Exception as e:
                    st.error(f"Error showing sources for {doc_name}: {str(e)}")
                
            except Exception as e:
                st.error(f"Error processing {doc_name}: {str(e)}")
                st.info(f"Using enhanced fallback for {doc_name}...")
                
                # Enhanced fallback method for this document
                try:
                    fallback_result = display_enhanced_fallback_single(query, retriever, api_key, doc_name)
                    all_responses[doc_name] = fallback_result
                except Exception as fallback_error:
                    st.error(f"Enhanced method also failed for {doc_name}: {str(fallback_error)}")
                    all_responses[doc_name] = f"Error: Could not process {doc_name}"
    
    # Store all responses in chat history
    if all_responses:
        chat_entry = {
            "query": query, 
            "response": all_responses,
            "document": "Multiple Documents: " + ", ".join(selected_docs),
            "timestamp": datetime.now().isoformat(),
            "agent_generated": True,
            "multi_document": True
        }
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append(chat_entry)

def process_single_document_query(query, api_key, retriever):
    """Process query for single document"""
    if not retriever:
        st.error(" No retriever available for the selected document. Please reprocess documents.")
        return
    
    try:
        # Use the enhanced multi-agent system
        with st.spinner("Initializing multi-agent system..."):
            crew = get_multiagent_system(api_key, retriever, use_enhanced=True)
        
        # Execute the multi-agent workflow
        with st.spinner("Multi-agent collaboration in progress..."):
            result = crew.kickoff(inputs={"query": query})
        
        # Display the result
        display_enhanced_answer(query, result, retriever)
        
    except Exception as e:
        st.error(f"Error during multi-agent execution: {str(e)}")
        st.info("Using enhanced fallback method...")
        
        # Enhanced fallback method
        try:
            display_enhanced_fallback(query, retriever, api_key)
        except Exception as fallback_error:
            st.error(f"Enhanced method also failed: {str(fallback_error)}")

def display_enhanced_fallback_single(query, retriever, api_key, doc_name):
    """Enhanced fallback method for single document in multi-document mode"""
    with st.spinner(f"Retrieving relevant content from {doc_name}..."):
        # Get relevant documents using compatible method
        docs = None
        try:
            if hasattr(retriever, 'invoke'):
                docs = retriever.invoke(query)
            elif hasattr(retriever, 'get_relevant_documents'):
                docs = retriever.get_relevant_documents(query)
            elif callable(retriever):
                docs = retriever(query)
        except Exception as e:
            st.error(f"Error retrieving documents from {doc_name}: {e}")
            return f"Error retrieving from {doc_name}"
        
        if not docs:
            st.warning(f"No relevant content found in {doc_name} for your query.")
            return f"No relevant content found in {doc_name}"
        
        # Combine context from top documents
        context_parts = []
        for i, doc in enumerate(docs[:4]):
            source = doc.metadata.get('source_file', 'Unknown')
            context_parts.append(f"Excerpt {i+1} from {source}:\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        # Generate detailed answer using Gemini
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Based ONLY on the content from {doc_name}, provide a comprehensive answer to the user's question.

User Question: {query}

Document: {doc_name}
Content:
{context}

Please provide a detailed answer that includes:

1. **DOCUMENT-SPECIFIC OVERVIEW**: Clear overview addressing the query specifically for {doc_name}
2. **KEY CONCEPTS FROM THIS DOCUMENT**: Detailed explanation of main concepts and ideas from {doc_name}
3. **SPECIFIC DETAILS**: Specific examples, data points, and details ONLY from {doc_name}
4. **STRUCTURED ORGANIZATION**: Clear sections with headings and bullet points
5. **COMPREHENSIVE COVERAGE**: Thorough coverage of all relevant aspects from this document

IMPORTANT: Only use information from {doc_name}. Do not include information from other documents.

Detailed Answer for {doc_name}:"""

        response = model.generate_content(prompt)
        
        st.markdown("##### Document-Specific Answer (Enhanced Fallback)")
        st.write(response.text)
        
        return response.text

def display_enhanced_answer(query, result, retriever):
    """Display enhanced answer with multi-agent details"""
    st.markdown("### Multi-Agent Generated Answer")
    
    # Show agent contribution breakdown
    with st.expander("Agent Contributions Breakdown", expanded=False):
        st.markdown("""
        **Agent Roles and Contributions:**
        
        **Document Retriever Agent**
        - Found relevant document chunks using semantic search
        - Retrieved contextual information from uploaded documents
        - Applied precision matching to query intent
        
        **Content Summarizer Agent** 
        - Condensed lengthy document content
        - Preserved all key information and context
        - Maintained relationships between concepts
        
        **Document Analyst Agent**
        - Extracted insights and patterns from documents
        - Identified key relationships and themes
        - Analyzed methodologies and approaches
        
        **Quality Assurance Agent**
        - Ensured professional formatting and structure
        - Added proper citations and references
        - Maintained academic presentation standards
        """)
    
    # Display the main answer
    st.write(result)
    
    # Show source information if available
    try:
        source_docs = None
        if hasattr(retriever, 'invoke'):
            source_docs = retriever.invoke(query)
        elif hasattr(retriever, 'get_relevant_documents'):
            source_docs = retriever.get_relevant_documents(query)
        elif callable(retriever):
            source_docs = retriever(query)
            
        if source_docs:
            with st.expander("Source Documents Used", expanded=False):
                for i, doc in enumerate(source_docs[:4]):
                    source_file = doc.metadata.get('source_file', 'Unknown')
                    st.markdown(f"**Source {i+1} - {source_file}:**")
                    st.text(f"{doc.page_content[:300]}...")
                    st.markdown("---")
    except:
        pass

    # Store in chat history
    chat_entry = {
        "query": query, 
        "response": result,
        "document": st.session_state.selected_document,
        "timestamp": datetime.now().isoformat(),
        "agent_generated": True
    }
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.chat_history.append(chat_entry)

def display_enhanced_fallback(query, retriever, api_key):
    """Enhanced fallback method with detailed answer generation"""
    with st.spinner("Retrieving relevant document content..."):
        # Get relevant documents using compatible method
        docs = None
        try:
            if hasattr(retriever, 'invoke'):
                docs = retriever.invoke(query)
            elif hasattr(retriever, 'get_relevant_documents'):
                docs = retriever.get_relevant_documents(query)
            elif callable(retriever):
                docs = retriever(query)
        except Exception as e:
            st.error(f"Error retrieving documents: {e}")
            return
        
        if not docs:
            st.warning("No relevant documents found for your query.")
            return
        
        # Combine context from top documents
        context_parts = []
        for i, doc in enumerate(docs[:6]):
            source = doc.metadata.get('source_file', 'Unknown')
            context_parts.append(f"Excerpt {i+1} from {source}:\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        # Generate detailed answer using Gemini
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Based on the following context from the uploaded document(s), provide a comprehensive and detailed answer to the user's question.

User Question: {query}

Document Context:
{context}

Please provide a detailed answer that includes:

1. **MAIN OVERVIEW**: Clear overview addressing the query
2. **KEY CONCEPTS**: Detailed explanation of main concepts and ideas  
3. **SPECIFIC DETAILS**: Specific examples, data points, and details from the documents
4. **STRUCTURED ORGANIZATION**: Clear sections with headings and bullet points
5. **SOURCE REFERENCES**: Citations to specific excerpts when mentioning information
6. **COMPREHENSIVE COVERAGE**: Thorough coverage of all relevant aspects

Format the response professionally with proper markdown formatting for readability.

Detailed Answer:"""

        response = model.generate_content(prompt)
        
        st.markdown("### Final Answer (Enhanced Fallback)")
        st.write(response.text)
        
        # Store in chat history
        chat_entry = {
            "query": query, 
            "response": response.text,
            "document": st.session_state.selected_document,
            "timestamp": datetime.now().isoformat(),
            "agent_generated": False,
            "sources_used": len(docs)
        }
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append(chat_entry)

def export_chat_as_json():
    """Export chat history as JSON"""
    if not st.session_state.get("chat_history"):
        st.warning("No chat history to export.")
        return
    
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "selected_document": st.session_state.get("selected_document", "Unknown"),
        "total_chats": len(st.session_state.chat_history),
        "multi_agent_system": True,
        "system_focus": "document-only",
        "chat_history": st.session_state.chat_history
    }
    
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="⬇️ Download JSON",
        data=json_str,
        file_name=f"multi_agent_chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key="json_export_final"
    )

def export_chat_as_markdown():
    """Export chat history as Markdown"""
    if not st.session_state.get("chat_history"):
        st.warning("No chat history to export.")
        return
    
    markdown_content = f"""# Multi-Agent Document Chat Export

**Document:** {st.session_state.get('selected_document', 'Unknown')}
**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Conversations:** {len(st.session_state.chat_history)}
**Multi-Agent System:** Active
**Focus:** Document-only processing

---

"""
    
    for i, chat in enumerate(st.session_state.chat_history, 1):
        agent_status = "Multi-Agent" if chat.get('agent_generated') else "Enhanced Fallback"
        markdown_content += f"""## Conversation {i} ({agent_status})

**Question:** {chat['query']}

**Answer:** {chat['response']}

**Document:** {chat.get('document', 'All Documents')}
**Timestamp:** {chat.get('timestamp', 'Unknown')}
**Sources Used:** {chat.get('sources_used', 'N/A')}

---

"""
    
    st.download_button(
        label="⬇️ Download Markdown",
        data=markdown_content,
        file_name=f"multi_agent_chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        key="markdown_export_final"
    )

def display_chat_history():
    """Display chat history in an organized way"""
    if st.session_state.get("chat_history"):
        st.markdown("---")
        st.markdown("## Chat History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history[-8:])):
            agent_indicator = "Multi-Agent" if chat.get('agent_generated') else "Fallback"
            with st.expander(f"{agent_indicator} {chat['query'][:70]}..." if len(chat['query']) > 70 else f"{agent_indicator} {chat['query']}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Document:** {chat.get('document', 'All Documents')}")
                with col2:
                    st.write(f"**Agent:** {'Multi-Agent' if chat.get('agent_generated') else 'Fallback'}")
                with col3:
                    st.write(f"**Sources:** {chat.get('sources_used', 'N/A')}")
                
                st.markdown("**Question:**")
                st.write(chat['query'])
                
                st.markdown("**Answer:**")
                
                # Handle both dict and string responses
                response = chat['response']
                if isinstance(response, dict):
                    # Multi-document response
                    for doc_name, doc_response in response.items():
                        st.markdown(f"**{doc_name}:**")
                        st.write(doc_response)
                        st.markdown("---")
                else:
                    # Single document response
                    st.write(response)
                
                if chat.get('timestamp'):
                    st.caption(f"Timestamp: {datetime.fromisoformat(chat['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")


def display_summary_in_chat(doc_name):
    """Display the summary for a document in the chat tab"""
    if 'document_summaries' not in st.session_state or doc_name not in st.session_state.document_summaries:
        st.warning(f"⚠️ No summary found for {doc_name}")
        return
    
    summary_data = st.session_state.document_summaries[doc_name]
    
    st.markdown("---")
    st.markdown(f"### Document Summary: {doc_name}")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        generated_time = datetime.fromisoformat(summary_data['generated_at']).strftime('%Y-%m-%d %H:%M')
        st.info(f"Generated: {generated_time}")
    with col2:
        st.info(f"Model: {summary_data['model']}")
    with col3:
        if st.button(" Close Summary", key="close_summary_in_chat"):
            st.session_state.show_summary_in_chat = False
            if 'summary_doc_name' in st.session_state:
                del st.session_state.summary_doc_name
            st.rerun()
    
    # Display summary content in an attractive format
    with st.container():
        st.markdown(summary_data['content'])
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(" Regenerate Summary", key="regenerate_summary_chat", use_container_width=True):
            from summary import generate_summary_for_document
            st.session_state.show_summary_in_chat = False
            generate_summary_for_document(doc_name)
    
    with col2:
        if st.button(" Copy to Clipboard", key="copy_summary_chat", use_container_width=True):
            st.code(summary_data['content'], language="markdown")
            st.info(" Copy from the code block above")
    
    with col3:
        # Create download content
        download_content = f"""# Document Summary: {doc_name}

**Generated:** {generated_time}
**Model:** {summary_data['model']}

---

{summary_data['content']}
"""
        st.download_button(
            label="⬇️ Download",
            data=download_content,
            file_name=f"summary_{doc_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="download_summary_chat",
            use_container_width=True
        )
    
    st.markdown("---")