"""NoteNest - AI-Powered Study Companion & Career Assistant.

Built with Streamlit, PyMuPDF, python-pptx, python-docx, Google Gemini/Gemma, and DuckDuckGo Live Search.
"""

import os
import sys
import io
import time
from typing import Dict, List, Any

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st
from modules.ingestor import DocumentIngestor, DocumentResult
from modules.gemma_agent import StudyCareerAgent
from modules.search_engine import WebSearchEngine

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NoteNest | AI Study & Career Companion",
    page_icon="🪺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Sleek CSS for Modern Dark/Glassmorphic Aesthetic
CUSTOM_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Gradient Headers */
    .hero-title {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.3rem;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* Environment Badge */
    .env-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #10b981;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-bottom: 1rem;
    }

    .env-badge .dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
    }

    /* Stat Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Flashcard UI */
    .flashcard-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        margin: 1rem 0;
        position: relative;
    }
    .card-badge {
        display: inline-block;
        background: #4f46e5;
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }
    .card-front {
        font-size: 1.25rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 1.2rem;
        line-height: 1.4;
    }
    .card-back {
        background: rgba(15, 23, 42, 0.7);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        color: #e2e8f0;
        font-size: 1.05rem;
        line-height: 1.5;
    }

    /* Grounding Pill */
    .grounding-banner {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .grounding-banner.notes {
        background: rgba(59, 130, 246, 0.12);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60a5fa;
    }
    .grounding-banner.web {
        background: rgba(168, 85, 247, 0.12);
        border: 1px solid rgba(168, 85, 247, 0.3);
        color: #c084fc;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "documents" not in st.session_state:
    st.session_state.documents = {}  # {filename: DocumentResult}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "cheat_sheet_content" not in st.session_state:
    st.session_state.cheat_sheet_content = ""
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "flashcards_csv" not in st.session_state:
    st.session_state.flashcards_csv = ""
if "project_guide_content" not in st.session_state:
    st.session_state.project_guide_content = ""
if "career_roadmap_content" not in st.session_state:
    st.session_state.career_roadmap_content = ""
if "current_card_index" not in st.session_state:
    st.session_state.current_card_index = 0
if "card_revealed" not in st.session_state:
    st.session_state.card_revealed = False

# Initialize Agent
@st.cache_resource
def get_agent():
    return StudyCareerAgent()

agent = get_agent()

# Helper to concatenate all loaded document text
def get_all_notes_text() -> str:
    if not st.session_state.documents:
        return ""
    combined = []
    for fname, doc_res in st.session_state.documents.items():
        combined.append(f"\n\n--- DOCUMENT: {fname} ---\n\n{doc_res.markdown}")
    return "\n".join(combined).strip()

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem;">
            <span style="font-size: 2rem;">🪺</span>
            <div>
                <h2 style="margin: 0; font-size: 1.4rem; font-weight: 800; color: #f8fafc;">NoteNest</h2>
                <p style="margin: 0; font-size: 0.75rem; color: #94a3b8;">AI Study & Career Companion</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Environment Status Indicator (Explicit Conda Requirement)
    conda_env = "notenest"
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    st.markdown(f"""
        <div class="env-badge">
            <span class="dot"></span>
            <span>Conda: <code>{conda_env}</code> (Py {py_version})</span>
        </div>
    """, unsafe_allow_html=True)
    
    # API Key Configuration
    with st.expander("🔑 API Configuration", expanded=not agent.is_configured):
        api_key_input = st.text_input(
            "Gemini / Google API Key",
            value=agent.api_key or "",
            type="password",
            help="Set via GOOGLE_API_KEY environment variable or enter here.",
        )
        if api_key_input and api_key_input != agent.api_key:
            agent.set_api_key(api_key_input)
            st.success("API key updated!")

        model_choice = st.selectbox(
            "Active Model",
            options=["gemma-4-26b-a4b-it", "gemma-4-31b-it"],
            index=0
        )
        agent.model_name = model_choice
    
    st.markdown("---")
    
    # Mode Selector Radio Button (Objective 4 Requirement)
    st.subheader("🎯 Primary Mode")
    mode_selection = st.radio(
        "Select Operating Mode",
        options=[
            "📁 Study Notes & Flashcards Mode",
            "🚀 Project & Career Roadmap Mode"
        ],
        index=0,
        label_visibility="collapsed"
    )

    # Search Grounding Toggle (Objective 4 Requirement)
    st.subheader("🔍 Grounding Mode")
    search_grounding = st.radio(
        "Context Source",
        options=[
            "📄 User Uploaded Resources",
            "🌐 Online Web Search"
        ],
        index=0,
        help="Select whether answers are grounded in your notes or live DuckDuckGo web results."
    )
    
    st.markdown("---")

    # Document Uploader (Objective 4 Requirement)
    st.subheader("📤 Document Ingestion")
    uploaded_files = st.file_uploader(
        "Upload Study Documents (.pdf, .pptx, .docx)",
        type=["pdf", "pptx", "docx"],
        accept_multiple_files=True,
        help="PyMuPDF visual block ordering for PDF, slide-by-slide for PPTX, paragraph-by-paragraph for DOCX."
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.documents:
                with st.spinner(f"Ingesting {uploaded_file.name}..."):
                    try:
                        doc_result = DocumentIngestor.ingest_file(uploaded_file, filename=uploaded_file.name)
                        st.session_state.documents[uploaded_file.name] = doc_result
                        st.toast(f"✅ Ingested {uploaded_file.name}", icon="📄")
                    except Exception as e:
                        st.error(f"Error parsing {uploaded_file.name}: {e}")

    # One-click sample loader button
    sample_files_available = [
        ("AI Engineering (Word)", "data/sample_ai_engineering.docx"),
        ("Cloud Architecture (PPTX)", "data/sample_cloud_architecture.pptx"),
        ("Python Concurrency (PDF)", "data/sample_python_concurrency.pdf")
    ]
    
    with st.expander("📚 Load Sample Datasets", expanded=False):
        st.caption("Quickly test NoteNest with pre-built study notes:")
        for label, rel_path in sample_files_available:
            abs_path = os.path.join(BASE_DIR, rel_path)
            if os.path.exists(abs_path):
                base_name = os.path.basename(abs_path)
                if st.button(f"Load {label}", key=f"load_{base_name}", use_container_width=True):
                    doc_res = DocumentIngestor.ingest_file(abs_path, filename=base_name)
                    st.session_state.documents[base_name] = doc_res
                    st.success(f"Loaded {base_name}!")
                    st.rerun()

    # Active Documents Overview
    if st.session_state.documents:
        st.markdown("#### 📂 Active Documents")
        for doc_name, doc_data in list(st.session_state.documents.items()):
            col_doc, col_del = st.columns([0.8, 0.2])
            with col_doc:
                st.caption(f"**{doc_name}** ({doc_data.file_type.upper()}) · {doc_data.stats.get('word_count', 0)} words")
            with col_del:
                if st.button("🗑️", key=f"del_{doc_name}", help="Remove document"):
                    del st.session_state.documents[doc_name]
                    st.rerun()
        
        if st.button("Clear All Notes", use_container_width=True):
            st.session_state.documents = {}
            st.session_state.cheat_sheet_content = ""
            st.session_state.flashcards = []
            st.session_state.flashcards_csv = ""
            st.rerun()

    st.markdown("---")
    st.caption("NoteNest v1.0 · Conda: `notenest`")


# -----------------------------------------------------------------------------
# MAIN CONTENT AREA: HEADER & METRICS
# -----------------------------------------------------------------------------
st.markdown('<div class="hero-title">NoteNest AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">High-Yield Study Synthesizer · Anki Flashcards · Project Architect · Context-Aware AI Tutor</div>', unsafe_allow_html=True)

# Grounding Status Pill
is_web_grounded = "online" in search_grounding.lower() or "web" in search_grounding.lower()
total_notes_words = sum(doc.stats.get("word_count", 0) for doc in st.session_state.documents.values())
doc_count = len(st.session_state.documents)

if is_web_grounded:
    st.markdown("""
        <div class="grounding-banner web">
            <span>🌐</span>
            <span><strong>Online Web Mode Active:</strong> Grounded in live DuckDuckGo real-time web searches, latest 2026 tech docs, and career trends.</span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="grounding-banner notes">
            <span>📄</span>
            <span><strong>User Notes Mode Active:</strong> Answers strictly grounded in {doc_count} uploaded document(s) ({total_notes_words:,} words total).</span>
        </div>
    """, unsafe_allow_html=True)

# Quick Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{doc_count}</div>
            <div class="metric-label">Ingested Files</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_notes_words:,}</div>
            <div class="metric-label">Parsed Words</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(st.session_state.flashcards)}</div>
            <div class="metric-label">Anki Flashcards</div>
        </div>
    """, unsafe_allow_html=True)
with col4:
    agent_status = "Ready" if agent.is_configured else "Key Needed"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number" style="font-size: 1.4rem; color: {'#10b981' if agent.is_configured else '#f59e0b'};">{agent_status}</div>
            <div class="metric-label">Gemma/Gemini Engine</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# -----------------------------------------------------------------------------
# THREE MAIN TABS (As Specified in Requirement 4)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📝 Cheat Sheet & Flashcards",
    "🧭 Career Roadmap & Project Architect",
    "💬 Interactive AI Note Tutor"
])


# =============================================================================
# TAB 1: 📝 CHEAT SHEET & FLASHCARDS
# =============================================================================
with tab1:
    st.markdown("### 📝 High-Yield Study Synthesizer & Anki Deck Generator")
    st.caption("Generate deduplicated summary cheat sheets and 1-click Anki-compatible flashcard decks from your uploaded notes.")
    
    notes_text = get_all_notes_text()
    if not notes_text:
        st.info("💡 **No study notes uploaded yet.** Upload PDF, PPTX, or DOCX files in the sidebar, or load the sample datasets to generate cheat sheets and flashcards.")
    
    col_cs_ctrl, col_fc_ctrl = st.columns(2)
    
    # Cheat Sheet Generator Column
    with col_cs_ctrl:
        st.markdown("#### ⚡ Master Cheat Sheet")
        focus_input = st.text_input(
            "Optional Focus Area", 
            placeholder="e.g., Focus on RAG latency trade-offs or GIL internals",
            help="Direct the AI synthesizer to emphasize a particular concept."
        )
        if st.button("🧠 Synthesize Master Cheat Sheet", use_container_width=True, disabled=not notes_text):
            if not agent.is_configured:
                st.error("Please configure your Google API Key in the sidebar or .env file.")
            else:
                with st.spinner("Synthesizing high-yield cheat sheet with Gemini..."):
                    try:
                        sheet_md = agent.generate_cheat_sheet(notes_text, focus_topic=focus_input)
                        st.session_state.cheat_sheet_content = sheet_md
                        st.toast("Master Cheat Sheet generated!", icon="✨")
                    except Exception as e:
                        st.error(f"Failed to generate cheat sheet: {e}")

    # Flashcard Generator Column
    with col_fc_ctrl:
        st.markdown("#### 🗂️ Anki Flashcard Deck")
        card_count = st.slider("Flashcard Count", min_value=5, max_value=25, value=10, step=1)
        if st.button("🎯 Generate Anki Flashcards", use_container_width=True, disabled=not notes_text):
            if not agent.is_configured:
                st.error("Please configure your Google API Key in the sidebar or .env file.")
            else:
                with st.spinner(f"Extracting {card_count} atomic flashcards..."):
                    try:
                        cards, csv_str = agent.generate_flashcards(notes_text, card_count=card_count)
                        st.session_state.flashcards = cards
                        st.session_state.flashcards_csv = csv_str
                        st.session_state.current_card_index = 0
                        st.session_state.card_revealed = False
                        st.toast(f"Generated {len(cards)} Anki Flashcards!", icon="🗂️")
                    except Exception as e:
                        st.error(f"Failed to generate flashcards: {e}")

    st.markdown("---")

    # Display Cheat Sheet Section
    if st.session_state.cheat_sheet_content:
        st.markdown("### 📋 Synthesized Cheat Sheet")
        col_down1, col_down2 = st.columns([0.8, 0.2])
        with col_down2:
            st.download_button(
                label="📥 Download Markdown",
                data=st.session_state.cheat_sheet_content,
                file_name="notenest_master_cheatsheet.md",
                mime="text/markdown",
                use_container_width=True
            )
        st.markdown(st.session_state.cheat_sheet_content)
        st.markdown("---")

    # Display Flashcards Section
    if st.session_state.flashcards:
        st.markdown("### 🗂️ Interactive Anki Flashcard Viewer")
        
        # 1-Click Anki CSV Download Button
        col_dl, col_help = st.columns([0.4, 0.6])
        with col_dl:
            st.download_button(
                label="📥 1-Click Download Anki CSV Deck",
                data=st.session_state.flashcards_csv,
                file_name="notenest_anki_deck.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_help:
            st.caption("ℹ️ **Anki Import**: Open Anki ➔ *File* ➔ *Import* ➔ Select this CSV ➔ Field 1 maps to Front, Field 2 maps to Back.")

        # Interactive Card Carousel
        cards = st.session_state.flashcards
        idx = st.session_state.current_card_index
        total_c = len(cards)
        
        if 0 <= idx < total_c:
            curr_card = cards[idx]
            
            st.markdown(f"""
                <div class="flashcard-box">
                    <div class="card-badge">Card {idx + 1} of {total_c}</div>
                    <div class="card-front">❓ {curr_card['front']}</div>
                </div>
            """, unsafe_allow_html=True)

            col_prev, col_flip, col_next = st.columns([0.25, 0.5, 0.25])
            with col_prev:
                if st.button("⬅️ Previous Card", disabled=(idx == 0), use_container_width=True):
                    st.session_state.current_card_index -= 1
                    st.session_state.card_revealed = False
                    st.rerun()
            with col_flip:
                reveal_label = "🙈 Hide Answer" if st.session_state.card_revealed else "👀 Reveal Answer"
                if st.button(reveal_label, use_container_width=True):
                    st.session_state.card_revealed = not st.session_state.card_revealed
                    st.rerun()
            with col_next:
                if st.button("Next Card ➡️", disabled=(idx == total_c - 1), use_container_width=True):
                    st.session_state.current_card_index += 1
                    st.session_state.card_revealed = False
                    st.rerun()

            if st.session_state.card_revealed:
                st.markdown(f"""
                    <div class="card-back">
                        <strong>💡 Answer:</strong><br>{curr_card['back']}
                    </div>
                """, unsafe_allow_html=True)

        # Full Deck Table Preview in Expander
        with st.expander(f"📖 View All {len(cards)} Flashcards in Deck", expanded=False):
            for i, c in enumerate(cards, 1):
                st.markdown(f"**{i}. {c['front']}**")
                st.markdown(f"> *{c['back']}*")
                st.write("")


# =============================================================================
# TAB 2: 🧭 CAREER ROADMAP & PROJECT ARCHITECT
# =============================================================================
with tab2:
    st.markdown("### 🧭 Career Roadmap & Project Architect Engine")
    st.caption("Plan production-ready portfolio projects with system architecture blueprints, or generate rigorous career progression roadmaps.")
    
    subtab_proj, subtab_career = st.tabs([
        "🏗️ How to Build [Project]",
        "🗺️ What Knowledge for [Career Path]"
    ])

    # -------------------------------------------------------------------------
    # Subtab 1: Project Guide Engine
    # -------------------------------------------------------------------------
    with subtab_proj:
        st.markdown("#### 🏗️ Project Architecture & Implementation Guide")
        
        proj_col1, proj_col2 = st.columns([0.65, 0.35])
        with proj_col1:
            project_input = st.text_input(
                "Project Name / Idea",
                value="Enterprise RAG Document Search with Hybrid Reranking",
                placeholder="e.g., Real-Time Distributed Chat with Kafka, Autonomous AI Agent"
            )
        with proj_col2:
            exp_level = st.selectbox(
                "Target Seniority Level",
                options=["Junior / Entry-Level", "Intermediate / Mid-Level", "Senior / Staff Architect"],
                index=1
            )
        
        tech_col1, tech_col2 = st.columns([0.7, 0.3])
        with tech_col1:
            tech_input = st.text_input(
                "Preferred Tech Stack / Constraints (Optional)",
                value="Python, FastAPI, PostgreSQL (pgvector), Docker, Next.js",
                placeholder="e.g. Go, Kubernetes, Kafka, Redis"
            )
        with tech_col2:
            st.write("")
            st.write("")
            gen_proj_btn = st.button("🚀 Generate Project Blueprint", use_container_width=True)

        # Quick project preset chips
        st.caption("💡 Quick Templates:")
        preset_cols = st.columns(4)
        if preset_cols[0].button("🤖 Autonomous Agent", use_container_width=True):
            project_input = "Autonomous Coding Agent with Tool Use & AST Validation"
        if preset_cols[1].button("💬 Distributed Chat", use_container_width=True):
            project_input = "High-Throughput WebSocket Chat with Kafka & Redis"
        if preset_cols[2].button("📊 Data Pipeline", use_container_width=True):
            project_input = "Real-Time Financial Streaming Pipeline with Flink & ClickHouse"
        if preset_cols[3].button("🔐 Auth & Microservices", use_container_width=True):
            project_input = "OAuth2 / OIDC Zero-Trust Microservices Mesh with Envoy"

        if gen_proj_btn:
            if not agent.is_configured:
                st.error("Please configure your Google API Key in the sidebar or .env file.")
            else:
                with st.spinner(f"Architecting blueprint for '{project_input}'..."):
                    try:
                        blueprint = agent.generate_project_guide(
                            project_name=project_input,
                            tech_stack=tech_input,
                            experience_level=exp_level
                        )
                        st.session_state.project_guide_content = blueprint
                        st.toast("Project blueprint ready!", icon="🏗️")
                    except Exception as e:
                        st.error(f"Error generating project guide: {e}")

        if st.session_state.project_guide_content:
            st.markdown("---")
            col_bp_title, col_bp_dl = st.columns([0.8, 0.2])
            with col_bp_dl:
                st.download_button(
                    "📥 Save Blueprint (.md)",
                    data=st.session_state.project_guide_content,
                    file_name="project_architecture_blueprint.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            st.markdown(st.session_state.project_guide_content)

    # -------------------------------------------------------------------------
    # Subtab 2: Career Roadmap Engine
    # -------------------------------------------------------------------------
    with subtab_career:
        st.markdown("#### 🗺️ Career Roadmap & Skill Tree Architect")
        
        c_col1, c_col2 = st.columns([0.65, 0.35])
        with c_col1:
            career_input = st.text_input(
                "Target Career Path / Role",
                value="Full-Stack AI & LLM Engineer",
                placeholder="e.g., Cloud Platform Engineer, Staff Backend Engineer, ML Systems Engineer"
            )
        with c_col2:
            timeline_months = st.slider("Target Timeline (Months)", min_value=3, max_value=12, value=6, step=3)

        skills_col1, skills_col2 = st.columns([0.7, 0.3])
        with skills_col1:
            curr_skills_input = st.text_input(
                "Current Baseline Skills",
                value="Intermediate Python, Basic SQL, Git, REST APIs",
                placeholder="e.g. JavaScript basics, CS degree student"
            )
        with skills_col2:
            st.write("")
            st.write("")
            gen_career_btn = st.button("🌟 Generate Career Roadmap", use_container_width=True)

        # Quick career preset chips
        st.caption("💡 Quick Role Targets:")
        role_cols = st.columns(4)
        if role_cols[0].button("🧠 AI/ML Engineer", use_container_width=True):
            career_input = "AI / ML Systems Engineer"
        if role_cols[1].button("☁️ Cloud Architect", use_container_width=True):
            career_input = "Cloud Solutions Architect (AWS/GCP)"
        if role_cols[2].button("⚡ Backend Engineer", use_container_width=True):
            career_input = "High-Performance Backend Engineer (Go & Python)"
        if role_cols[3].button("🛡️ Cyber Security", use_container_width=True):
            career_input = "Application Security & DevSecOps Engineer"

        if gen_career_btn:
            if not agent.is_configured:
                st.error("Please configure your Google API Key in the sidebar or .env file.")
            else:
                with st.spinner(f"Designing comprehensive career roadmap for '{career_input}'..."):
                    try:
                        roadmap = agent.generate_career_roadmap(
                            career_path=career_input,
                            current_skills=curr_skills_input,
                            target_timeline_months=timeline_months
                        )
                        st.session_state.career_roadmap_content = roadmap
                        st.toast("Career roadmap synthesized!", icon="🗺️")
                    except Exception as e:
                        st.error(f"Error generating roadmap: {e}")

        if st.session_state.career_roadmap_content:
            st.markdown("---")
            col_rm_title, col_rm_dl = st.columns([0.8, 0.2])
            with col_rm_dl:
                st.download_button(
                    "📥 Save Roadmap (.md)",
                    data=st.session_state.career_roadmap_content,
                    file_name="career_roadmap.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            st.markdown(st.session_state.career_roadmap_content)


# =============================================================================
# TAB 3: 💬 INTERACTIVE AI NOTE TUTOR
# =============================================================================
with tab3:
    st.markdown("### 💬 Interactive AI Study Tutor & Research Assistant")
    
    # Mode Clarification Pill in Tab 3
    if is_web_grounded:
        st.caption("🌐 **Mode**: Online Web Mode. The tutor performs live DuckDuckGo searches to answer queries with fresh documentation and citations.")
    else:
        st.caption("📄 **Mode**: User Notes Mode. The tutor strictly adheres to your uploaded PDFs, PPTXs, and Word files, citing specific pages and slides.")

    # Chat Clear Button
    col_chat_title, col_chat_clear = st.columns([0.8, 0.2])
    with col_chat_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Display Conversation History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("🔗 Grounding Citations & Sources", expanded=False):
                    for src in message["sources"]:
                        if src.get("href"):
                            st.markdown(f"- [{src.get('title', 'Web Link')}]({src.get('href')})")
                            st.caption(f"  {src.get('body', '')}")
                        elif src.get("type") == "user_notes":
                            st.markdown("- Grounded strictly in uploaded student notes & slides.")

    # Suggested Prompts Chips
    st.caption("💡 Suggested questions:")
    chip_cols = st.columns(3)
    prompt_to_send = None
    if chip_cols[0].button("❓ What are the core trade-offs discussed?", use_container_width=True):
        prompt_to_send = "What are the core architectural trade-offs discussed in these materials?"
    if chip_cols[1].button("⚠️ What common traps should I avoid?", use_container_width=True):
        prompt_to_send = "What are the most common misconceptions or exam gotchas for this topic?"
    if chip_cols[2].button("🌐 What are the latest 2026 industry standards?", use_container_width=True):
        prompt_to_send = "What are the latest 2026 industry standards, best practices, and career demands for this domain?"

    # Chat Input Box
    user_query = st.chat_input("Ask a question about your notes or career guidance...")
    active_prompt = prompt_to_send or user_query

    if active_prompt:
        if not agent.is_configured:
            st.error("Please configure your Google API Key in the sidebar or .env file.")
        else:
            # Append user message
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.markdown(active_prompt)

            # Generate Assistant Response
            with st.chat_message("assistant"):
                status_placeholder = st.empty()
                if is_web_grounded:
                    status_placeholder.markdown("🔍 *Searching live web with DuckDuckGo...*")
                else:
                    status_placeholder.markdown("📖 *Scanning uploaded study notes & slides...*")
                
                try:
                    notes_ctx = get_all_notes_text()
                    result = agent.answer_tutor_query(
                        query=active_prompt,
                        chat_history=st.session_state.chat_history,
                        search_mode="online_search" if is_web_grounded else "user_notes",
                        user_notes_context=notes_ctx
                    )
                    status_placeholder.empty()

                    assistant_text = result["answer"]
                    sources = result.get("sources", [])
                    st.markdown(assistant_text)

                    if sources and is_web_grounded:
                        with st.expander("🔗 Grounding Citations & Sources", expanded=False):
                            for src in sources:
                                if src.get("href"):
                                    st.markdown(f"- [{src.get('title', 'Web Link')}]({src.get('href')})")
                                    st.caption(f"  {src.get('body', '')}")
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": assistant_text,
                        "sources": sources
                    })
                except Exception as e:
                    status_placeholder.empty()
                    err_msg = f"⚠️ Error answering query: {e}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
