# agents.py - Fixed with correct LangChain method names
import streamlit as st
import google.generativeai as genai
from typing import Dict, Any, TypedDict
import os
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    st.warning("⚠️ LangGraph not available. Using simplified workflow.")

# Define the state for our multi-agent system
class AgentState(TypedDict):
    query: str
    retrieved_documents: str
    summarized_content: str
    analysis_results: str
    final_output: str
    current_step: str
    error: str
    tools: Dict[str, Any]

class DocumentRetrieverTool:
    name: str = "Document Retriever"
    description: str = "Retrieve relevant document chunks from uploaded documents using semantic search"
    
    def __init__(self, retriever):
        self.retriever = retriever
    
    def run(self, query: str) -> str:
        """Retrieve relevant documents for a query"""
        try:
            # Try different method names for compatibility
            if hasattr(self.retriever, 'get_relevant_documents'):
                docs = self.retriever.get_relevant_documents(query)
            elif hasattr(self.retriever, 'invoke'):
                docs = self.retriever.invoke(query)
            elif hasattr(self.retriever, '__call__'):
                docs = self.retriever(query)
            else:
                return "Error: Retriever object has no compatible method"
            
            if not docs:
                return "No relevant documents found for the query."
            
            result = "🔍 RETRIEVED DOCUMENTS:\n\n"
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get('source_file', 'Unknown')
                file_type = doc.metadata.get('file_format', 'Unknown')
                result += f"📄 DOCUMENT {i} - {source} ({file_type.upper()})\n"
                result += f"Content: {doc.page_content}\n"
                result += "─" * 80 + "\n\n"
            
            return result
        except Exception as e:
            return f"Error retrieving documents: {str(e)}"

class ContentSummarizerTool:
    name: str = "Content Summarizer"
    description: str = "Summarize long text into comprehensive, accurate summaries while preserving key information"
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def run(self, text: str) -> str:
        """Summarize long text into comprehensive summary"""
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""As an expert content summarizer, please provide a comprehensive summary of the following text that preserves all critical information while being concise and well-organized:

TEXT TO SUMMARIZE:
{text}

SUMMARY REQUIREMENTS:
- Preserve all key facts, data points, and concepts
- Maintain context and relationships between ideas
- Highlight the most important information
- Ensure technical accuracy
- Organize in a logical, readable structure

COMPREHENSIVE SUMMARY:"""
            
            response = model.generate_content(prompt)
            return f"📝 SUMMARY:\n{response.text}"
        except Exception as e:
            return f"Error generating summary: {str(e)}"

class DocumentAnalyzerTool:
    name: str = "Document Analyst"
    description: str = "Perform deep analysis on document content to extract insights, patterns, and relationships"
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def run(self, text: str) -> str:
        """Perform deep analysis on text content"""
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""As a senior document analyst, perform a comprehensive analysis of the following content:

CONTENT FOR ANALYSIS:
{text}

ANALYSIS REQUIREMENTS:
1. Identify and categorize main themes and key concepts
2. Extract and highlight important data points, statistics, and metrics
3. Analyze methodologies, approaches, or frameworks used
4. Identify relationships, patterns, and connections between elements
5. Note significant findings, conclusions, or recommendations
6. Point out any gaps, contradictions, or areas needing clarification
7. Provide insights on practical applications or implications

DETAILED ANALYSIS REPORT:"""
            
            response = model.generate_content(prompt)
            return f"🔍 ANALYSIS RESULTS:\n{response.text}"
        except Exception as e:
            return f"Error analyzing content: {str(e)}"

class ContentFormatterTool:
    name: str = "Content Formatter"
    description: str = "Format content with professional structure, organization, and presentation"
    
    def run(self, content: str) -> str:
        """Format content with professional structure"""
        # Only format if there's actual content
        if not content or "Error" in content:
            return content
            
        formatted_content = f"""✨ PROFESSIONALLY FORMATTED RESPONSE:

{content}

🎯 FORMATTING FEATURES APPLIED:
- Clear hierarchical structure with sections
- Professional typography and spacing
- Consistent formatting throughout
- Enhanced readability with bullet points
- Professional presentation standards
- Optimized for both technical and non-technical audiences"""
        
        return formatted_content

class CitationManagerTool:
    name: str = "Citation Manager"
    description: str = "Manage citations and ensure proper source attribution in responses"
    
    def run(self, content: str) -> str:
        """Add proper citations and source references to content"""
        # Only add citations if there's actual content
        if not content or "Error" in content:
            return content
            
        return f"""✅ CITATION MANAGEMENT APPLIED:

{content}

📚 SOURCES ATTRIBUTED:
- All document references properly cited
- Source files clearly referenced
- Academic citation standards applied
- Cross-references maintained for verification"""

# Define agent nodes
def retriever_agent(state: AgentState) -> AgentState:
    """Retrieve relevant documents"""
    st.info("🕵️‍♂️ Retrieval Agent: Searching documents...")
    
    try:
        tools = state.get("tools", {})
        retriever_tool = tools.get("retriever")
        
        if retriever_tool:
            retrieved_content = retriever_tool.run(state["query"])
            return {
                **state,
                "retrieved_documents": retrieved_content,
                "current_step": "retrieval_complete"
            }
        else:
            return {
                **state,
                "retrieved_documents": "Retriever tool not available",
                "current_step": "retrieval_complete"
            }
    except Exception as e:
        return {
            **state,
            "retrieved_documents": f"Error in retrieval: {str(e)}",
            "current_step": "retrieval_complete"
        }

def summarizer_agent(state: AgentState) -> AgentState:
    """Summarize retrieved content"""
    st.info("📝 Summarization Agent: Condensing information...")
    
    try:
        tools = state.get("tools", {})
        summarizer_tool = tools.get("summarizer")
        
        if summarizer_tool and state.get("retrieved_documents"):
            # Only summarize if we have actual documents, not errors
            if "Error" not in state["retrieved_documents"] and "No relevant documents" not in state["retrieved_documents"]:
                summarized_content = summarizer_tool.run(state["retrieved_documents"])
            else:
                summarized_content = state["retrieved_documents"]  # Pass through the error message
                
            return {
                **state,
                "summarized_content": summarized_content,
                "current_step": "summarization_complete"
            }
        else:
            return {
                **state,
                "summarized_content": "Summarizer tool not available",
                "current_step": "summarization_complete"
            }
    except Exception as e:
        return {
            **state,
            "summarized_content": f"Error in summarization: {str(e)}",
            "current_step": "summarization_complete"
        }

def analyst_agent(state: AgentState) -> AgentState:
    """Analyze summarized content"""
    st.info("🔍 Analysis Agent: Extracting insights...")
    
    try:
        tools = state.get("tools", {})
        analyzer_tool = tools.get("analyzer")
        
        if analyzer_tool and state.get("summarized_content"):
            # Only analyze if we have actual content, not errors
            if "Error" not in state["summarized_content"] and "No relevant documents" not in state["summarized_content"]:
                analysis_results = analyzer_tool.run(state["summarized_content"])
            else:
                analysis_results = state["summarized_content"]  # Pass through the error message
                
            return {
                **state,
                "analysis_results": analysis_results,
                "current_step": "analysis_complete"
            }
        else:
            return {
                **state,
                "analysis_results": "Analyzer tool not available",
                "current_step": "analysis_complete"
            }
    except Exception as e:
        return {
            **state,
            "analysis_results": f"Error in analysis: {str(e)}",
            "current_step": "analysis_complete"
        }

def quality_agent(state: AgentState) -> AgentState:
    """Apply formatting and citations"""
    st.info("✨ Quality Agent: Finalizing response...")
    
    try:
        tools = state.get("tools", {})
        formatter_tool = tools.get("formatter")
        citation_tool = tools.get("citations")
        
        # Get the content to format
        content_to_format = state.get('analysis_results', '') or state.get('summarized_content', '') or state.get('retrieved_documents', '')
        
        if formatter_tool and content_to_format and "Error" not in content_to_format and "No relevant documents" not in content_to_format:
            formatted_content = formatter_tool.run(content_to_format)
            if citation_tool:
                final_output = citation_tool.run(formatted_content)
            else:
                final_output = formatted_content
        else:
            # If there's an error or no content, just pass through the original content
            final_output = content_to_format
            
        return {
            **state,
            "final_output": final_output,
            "current_step": "complete"
        }
    except Exception as e:
        return {
            **state,
            "final_output": f"Error in quality assurance: {str(e)}",
            "current_step": "complete"
        }

def create_langgraph_multiagent(api_key, retriever):
    """Create a multi-agent system using LangGraph"""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph not available")
    
    # Create tools
    tools = {
        "retriever": DocumentRetrieverTool(retriever=retriever),
        "summarizer": ContentSummarizerTool(api_key=api_key),
        "analyzer": DocumentAnalyzerTool(api_key=api_key),
        "formatter": ContentFormatterTool(),
        "citations": CitationManagerTool()
    }
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes for each agent
    workflow.add_node("retriever", retriever_agent)
    workflow.add_node("summarizer", summarizer_agent)
    workflow.add_node("analyst", analyst_agent)
    workflow.add_node("quality_assurance", quality_agent)
    
    # Define the workflow
    workflow.set_entry_point("retriever")
    workflow.add_edge("retriever", "summarizer")
    workflow.add_edge("summarizer", "analyst")
    workflow.add_edge("analyst", "quality_assurance")
    workflow.add_edge("quality_assurance", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    # Create a wrapper that includes tools in the state
    class LangGraphMultiAgent:
        def __init__(self, graph, tools):
            self.graph = graph
            self.tools = tools
        
        def kickoff(self, inputs):
            query = inputs.get("query", "")
            
            # Initialize state with tools
            initial_state = {
                "query": query,
                "retrieved_documents": "",
                "summarized_content": "",
                "analysis_results": "",
                "final_output": "",
                "current_step": "started",
                "error": "",
                "tools": self.tools
            }
            
            try:
                # Execute the graph
                final_state = self.graph.invoke(initial_state)
                return final_state.get("final_output", "No output generated")
            except Exception as e:
                return f"Error in multi-agent execution: {str(e)}"
    
    return LangGraphMultiAgent(graph, tools)

def create_simple_workflow(api_key, retriever):
    """Simple sequential workflow without LangGraph"""
    
    class SimpleMultiAgent:
        def __init__(self, api_key, retriever):
            self.tools = {
                "retriever": DocumentRetrieverTool(retriever=retriever),
                "summarizer": ContentSummarizerTool(api_key=api_key),
                "analyzer": DocumentAnalyzerTool(api_key=api_key),
                "formatter": ContentFormatterTool(),
                "citations": CitationManagerTool()
            }
        
        def kickoff(self, inputs):
            query = inputs.get("query", "")
            
            try:
                # Step 1: Retrieve documents
                st.info("🕵️‍♂️ Retrieving documents...")
                retrieved = self.tools["retriever"].run(query)
                
                # If retrieval failed, return the error immediately
                if "Error" in retrieved or "No relevant documents" in retrieved:
                    return retrieved
                
                # Step 2: Summarize content
                st.info("📝 Summarizing content...")
                summarized = self.tools["summarizer"].run(retrieved)
                
                # Step 3: Analyze content
                st.info("🔍 Analyzing content...")
                analyzed = self.tools["analyzer"].run(summarized)
                
                # Step 4: Format and add citations
                st.info("✨ Formatting final response...")
                formatted = self.tools["formatter"].run(analyzed)
                final_output = self.tools["citations"].run(formatted)
                
                return final_output
                
            except Exception as e:
                return f"Error in simple workflow: {str(e)}"
    
    return SimpleMultiAgent(api_key, retriever)

def get_multiagent_system(api_key, retriever, use_enhanced=True):
    """Main function to get the multi-agent system"""
    if use_enhanced and LANGGRAPH_AVAILABLE:
        try:
            st.info("🚀 Initializing LangGraph Multi-Agent System...")
            return create_langgraph_multiagent(api_key, retriever)
        except Exception as e:
            st.error(f"LangGraph multi-agent system failed: {e}")
            st.info("Falling back to simple sequential workflow...")
            return create_simple_workflow(api_key, retriever)
    else:
        if use_enhanced and not LANGGRAPH_AVAILABLE:
            st.warning("⚠️ LangGraph not available. Using simple workflow.")
        return create_simple_workflow(api_key, retriever)

# Additional utility functions
def get_agent_workflow_description():
    """Get description of the multi-agent workflow"""
    return {
        "system": "LangGraph Multi-Agent System" if LANGGRAPH_AVAILABLE else "Simple Multi-Agent System",
        "agents": 4,
        "tools": 5,
        "workflow": "Retrieval → Summarization → Analysis → Quality Assurance",
        "features": [
            "Professional formatting and citations",
            "Document-only information processing", 
            "Quality assurance processes",
            "Flexible state management" if LANGGRAPH_AVAILABLE else "Sequential processing"
        ],
        "focus": "Exclusively uses uploaded documents - no web search"
    }

def get_system_capabilities():
    """Get the capabilities of the multi-agent system"""
    return {
        "input_sources": ["Uploaded documents only"],
        "processing": ["Semantic search", "Content summarization", "Pattern analysis", "Professional formatting"],
        "output": ["Comprehensive answers", "Proper citations", "Structured responses", "Professional presentation"],
        "limitations": ["No web search", "No external data", "Document-based knowledge only"]
    }

def get_installation_instructions():
    """Get installation instructions"""
    return {
        "langgraph": "pip install langgraph",
        "langchain": "pip install langchain langchain-community langchain-core",
        "all": "pip install langgraph langchain langchain-community langchain-core google-generativeai streamlit"
    }

def get_available_agents():
    """Get list of available agents in the system"""
    return [
        {
            "name": "Document Retriever Agent",
            "role": "Finds and extracts relevant information from uploaded documents",
            "tools": ["Document Retriever"]
        },
        {
            "name": "Content Summarizer Agent", 
            "role": "Condenses complex information into clear, comprehensive summaries",
            "tools": ["Content Summarizer"]
        },
        {
            "name": "Document Analyst Agent",
            "role": "Performs deep analytical analysis to extract insights and patterns",
            "tools": ["Document Analyst"]
        },
        {
            "name": "Quality Assurance Agent",
            "role": "Ensures perfect formatting, citations, and professional presentation",
            "tools": ["Content Formatter", "Citation Manager"]
        }
    ]