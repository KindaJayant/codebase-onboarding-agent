import streamlit as st
import os
import json
from dotenv import load_dotenv

from agent.graph import build_graph
from utils import vectorstore

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Codebase Onboarding Agent", layout="wide", page_icon="🕵️")

# UI Styling
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #ffffff;
}
.report-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: #4da6ff;
}
</style>
""", unsafe_allow_html=True)

st.title("🕵️ Codebase Onboarding Agent")
st.markdown("Automated analysis for senior-developer onboarding.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    repo_url = st.text_input("GitHub Repo URL", placeholder="https://github.com/user/repo")
    api_key = st.text_input("Gemini API Key", value=GEMINI_API_KEY or "", type="password")
    
    if st.button("🚀 Analyze Repository"):
        if not repo_url or not api_key:
            st.error("Please provide both Repo URL and API Key.")
        else:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            st.session_state.repo_name = repo_name
            st.session_state.repo_url = repo_url
            st.session_state.api_key = api_key
            
            # Form LangGraph initial state
            initial_state = {
                "repo_url": repo_url,
                "repo_name": repo_name,
                "api_key": api_key, # API key now passed via state
            }
            
            with st.status("Analyzing codebase...", expanded=True) as status:
                st.write("🔍 Extracting code architecture...")
                graph = build_graph()
                final_state = graph.invoke(initial_state)
                
                if final_state.get('error'):
                    st.error(f"Error during analysis:\n\n{final_state['error']}")
                else:
                    st.session_state.final_state = final_state
                    st.write("📂 Codebase analyzed!")
                    
                    # Also build vectorstore
                    st.write("🧠 Indexing into ChromaDB for semantic search...")
                    try:
                        vectorstore.initialize_vector_store(
                            final_state['repo_path'], 
                            repo_name, 
                            api_key
                        )
                        st.write("✅ Vectorstore ready.")
                    except Exception as e:
                        st.warning(f"Vector search might be degraded (error indexing: {e})")
                        
                    status.update(label="Analysis Finished!", state="complete", expanded=False)

# Main Content
if 'final_state' in st.session_state:
    state = st.session_state.final_state
    
    if state.get('error'):
        st.error(state['error'])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🚪 Entry Points & Map", 
            "🛠️ Tech Details",
            "🌊 Gotchas & Flow",
            "🔍 Code Search"
        ])
        
        with tab1:
            st.header("Senior Developer Report")
            st.markdown(state.get('report', "No report generated."))
            
        with tab2:
            st.header("Entry Points")
            st.markdown(state.get('entry_points', "No entry points found."))
            st.divider()
            st.header("Module Map")
            st.markdown(state.get('module_summaries', ""))
                
        with tab3:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Tech Stack JSON")
                st.json(state.get('tech_stack', {}))
            with col2:
                st.subheader("Repository Structure")
                st.code(state.get('structure', ""), language='text')
                    
        with tab4:
            st.header("Data Flow")
            st.markdown(state.get('data_flow', "No data flow extracted."))
            st.divider()
            st.header("Gotchas & Warnings")
            st.markdown(state.get('gotchas', ""))
                
        with tab5:
            st.header("Semantic Code Search")
            query = st.text_input("Ask a question about the code...", placeholder="e.g., How does authentication work?")
            if query:
                results = vectorstore.search_codebase(
                    st.session_state.repo_name, 
                    query, 
                    st.session_state.api_key
                )
                
                if results and 'error' not in results and results['documents'] and results['documents'][0]:
                    docs = results['documents'][0]
                    metas = results['metadatas'][0]
                    for idx, doc in enumerate(docs):
                        meta = metas[idx]
                        file_path = meta.get('file', 'Unknown')
                        with st.expander(f"Result {idx+1} from `{file_path}`"):
                            st.code(doc)
                else:
                    st.warning("No results or error during search.")
else:
    st.info("👈 Enter a GitHub URL in the sidebar to get started.")
    st.image("https://img.freepik.com/free-vector/modern-onboarding-design_52683-36696.jpg", use_container_width=True)
