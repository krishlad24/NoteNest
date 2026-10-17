"""Gemma & Gemini Study & Career Agent for NoteNest.

Features:
A. Study Synthesizer & Anki Flashcard Generator.
B. Project Architect & Career Roadmap Engine.
C. Interactive Context-Aware Tutor with User Notes vs. Live Web Search grounding.
"""

import csv
import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from dotenv import load_dotenv

from modules.search_engine import WebSearchEngine

# Load environment variables
load_dotenv()
logger = logging.getLogger("notenest.agent")


class StudyCareerAgent:
    """Core AI companion powered by Gemini / Gemma models."""

    DEFAULT_MODEL = "gemma-4-26b-a4b-it"
    FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-pro-latest"]

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the agent with Gemini/Gemma credentials."""
        self.api_key = (
            api_key 
            or os.getenv("GOOGLE_API_KEY") 
            or os.getenv("GEMINI_API_KEY")
        )
        self.model_name = model_name or self.DEFAULT_MODEL
        self._is_configured = False
        self._client = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._is_configured = True
            except Exception as e:
                logger.error(f"Failed to configure Google Generative AI: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if API key is active."""
        return self._is_configured and bool(self.api_key)

    def set_api_key(self, api_key: str):
        """Update API key at runtime."""
        self.api_key = api_key.strip()
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self._is_configured = True
            self._client = None

    def get_model(self, model_name: Optional[str] = None) -> genai.GenerativeModel:
        """Get or initialize GenerativeModel instance."""
        target_model = model_name or self.model_name
        return genai.GenerativeModel(target_model)

    def _call_llm(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.4) -> str:
        """Robust LLM invocation with model fallback."""
        if not self.is_configured:
            raise ValueError(
                "Gemini API Key is not configured. Please supply a valid GOOGLE_API_KEY or GEMINI_API_KEY in .env or the sidebar."
            )

        candidate_models = [self.model_name] + [m for m in self.FALLBACK_MODELS if m != self.model_name]
        last_error = None

        for model_id in candidate_models:
            try:
                model_kwargs = {}
                if system_instruction:
                    try:
                        model_kwargs["system_instruction"] = system_instruction
                    except Exception:
                        pass
                
                model = genai.GenerativeModel(model_id, **model_kwargs)
                gen_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=0.95,
                    max_output_tokens=4096
                )
                
                response = model.generate_content(prompt, generation_config=gen_config)
                if response and hasattr(response, "text") and response.text:
                    return response.text.strip()
                elif response and hasattr(response, "parts"):
                    text_parts = [p.text for p in response.parts if hasattr(p, "text")]
                    if text_parts:
                        return "".join(text_parts).strip()
            except Exception as e:
                last_error = e
                logger.warning(f"Error calling model '{model_id}': {e}. Attempting fallback...")
                continue

        raise RuntimeError(f"All candidate models failed. Last error: {last_error}")

    # =========================================================================
    # FEATURE A: Study Synthesizer & Anki Flashcard Generator
    # =========================================================================

    def generate_cheat_sheet(self, note_text: str, focus_topic: str = "") -> str:
        """Generate a high-yield, deduplicated Markdown cheat sheet from user notes."""
        system_instruction = (
            "You are NoteNest's Chief Academic Synthesizer. Your job is to transform raw, verbose "
            "student notes, slides, and textbooks into ultra-dense, visually organized, high-yield cheat sheets. "
            "Use clear Markdown formatting, emojis, bold key terms, trade-off tables, and exam trap alerts."
        )

        focus_prompt = f"\nSpecific Focus Area requested by user: {focus_topic}\n" if focus_topic else ""

        prompt = f"""
Analyze the following user notes and produce a comprehensive, master-level Cheat Sheet.

Structure your output into these clean sections:
# 🧠 Master Cheat Sheet: Key Insights & Synthesized Concepts
1. **Executive Mental Model**: A 2-3 sentence intuitive explanation of the core idea.
2. **Key Terms & Foundational Axioms**: Concise definitions with bold keywords.
3. **Comparative Analysis / Trade-Off Matrix**: A markdown table comparing components, methods, or algorithms.
4. **Critical Rules, Formulas & Syntax**: Actionable code snippets or math formulas if applicable.
5. **⚠️ High-Frequency Traps & Exam Gotchas**: Common misconceptions and subtle gotchas students miss.
6. **Summary Quick-Recall Checklist**: 5 bullet points to review right before an exam or interview.

{focus_prompt}
---
### USER SOURCE NOTES:
{note_text}
---
"""
        return self._call_llm(prompt, system_instruction=system_instruction, temperature=0.3)

    def generate_flashcards(self, note_text: str, card_count: int = 12) -> Tuple[List[Dict[str, str]], str]:
        """Generate high-yield QA flashcards and export an Anki-compatible CSV string.
        
        Returns:
            Tuple of:
            - List of card dicts: [{'front': ..., 'back': ...}]
            - CSV string: RFC 4180 standard Front,Back CSV ready for 1-click Anki import.
        """
        system_instruction = (
            "You are an expert cognitive learning specialist specializing in spaced repetition (Anki). "
            "Extract atomic, highly memorable flashcards following the minimum information principle. "
            "Each question should test ONE specific concept. The answer should be concise, authoritative, and direct."
        )

        prompt = f"""
From the notes below, extract exactly {card_count} high-yield flashcards.
Output your response STRICTLY as a valid JSON array of objects with "front" and "back" keys.
Do not wrap in anything other than a standard markdown json codeblock.

Format:
```json
[
  {{
    "front": "What is the primary trade-off of X?",
    "back": "X provides Y at the expense of Z because..."
  }}
]
```

---
### USER SOURCE NOTES:
{note_text}
---
"""
        response_text = self._call_llm(prompt, system_instruction=system_instruction, temperature=0.3)
        
        # Parse JSON
        cards = []
        try:
            # Extract JSON block
            json_match = re.search(r"```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text.strip()
                # Clean up if starts with ```
                if json_str.startswith("```"):
                    json_str = re.sub(r"^```(?:json)?", "", json_str).rstrip("`").strip()
            
            parsed_data = json.loads(json_str)
            for item in parsed_data:
                front = str(item.get("front", "")).strip()
                back = str(item.get("back", "")).strip()
                if front and back:
                    cards.append({"front": front, "back": back})
        except Exception as e:
            logger.warning(f"JSON parsing error for flashcards: {e}. Falling back to line parsing.")
            # Fallback line regex parsing
            pairs = re.findall(r'(?:Q|Front|Question):\s*(.*?)\s*(?:A|Back|Answer):\s*(.*?)(?=(?:Q|Front|Question):|$)', response_text, re.DOTALL | re.IGNORECASE)
            for q, a in pairs:
                if q.strip() and a.strip():
                    cards.append({"front": q.strip(), "back": a.strip()})

        # If still empty, create fallback cards from lines
        if not cards:
            cards = [{"front": "Overview of provided notes", "back": note_text[:200] + "..."}]

        # Generate Anki-compatible RFC-4180 CSV
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_MINIMAL)
        
        # Header row (optional in Anki, but standard Front,Back)
        csv_writer.writerow(["Front", "Back"])
        for card in cards:
            csv_writer.writerow([card["front"], card["back"]])
            
        csv_content = csv_buffer.getvalue()
        return cards, csv_content

    # =========================================================================
    # FEATURE B: Career Roadmap & Project Guide Engine
    # =========================================================================

    def generate_project_guide(
        self, 
        project_name: str, 
        tech_stack: str = "", 
        experience_level: str = "Intermediate"
    ) -> str:
        """Generate architectural blueprints and step-by-step phases for building a specific project."""
        system_instruction = (
            "You are a Principal Software Architect and Engineering Career Advisor. "
            "You provide pragmatic, production-grade technical plans for building ambitious portfolio projects. "
            "Always include architecture diagrams (Mermaid format), realistic tech stack choices with trade-offs, "
            "and phase-by-phase milestones from MVP to production."
        )

        tech_prompt = f"Preferred Tech Stack / Constraints: {tech_stack}" if tech_stack else "Select the modern industry standard tech stack."

        prompt = f"""
Create a comprehensive, production-grade Engineering Project Blueprint for:
# 🚀 Project Name: "{project_name}"
Target Level: {experience_level}
{tech_prompt}

Please structure your guide into the following sections:
1. **System Vision & Core Value Proposition**: What problem does this solve and why is it impressive on a resume?
2. **Architecture & Component Diagram**: Provide a valid ```mermaid graph TD diagram showing data flow between client, API gateway, services, database, cache, and external APIs.
3. **Recommended Tech Stack & Justifications**:
   - Client / UI: (Framework & reasons)
   - Backend / APIs: (Language, framework, protocol e.g. REST/gRPC/GraphQL)
   - Data Layer: (Relational vs NoSQL vs Vector vs Cache)
   - Infrastructure & Deployment: (Docker, CI/CD, Cloud)
4. **Step-by-Step Implementation Roadmap**:
   - **Phase 1: Minimal Viable Architecture (MVP)** (Core schemas, basic endpoints, working prototype)
   - **Phase 2: Scalability, Caching & Resilience** (Redis caching, rate limiting, connection pooling)
   - **Phase 3: Production Readiness & Observability** (Structured logging, OpenTelemetry, unit & integration tests)
   - **Phase 4: Advanced Features & Polish** (AI integrations, WebSockets, background workers)
5. **Senior Engineering Pitfalls**: 3 critical architectural mistakes junior engineers make when building this.
6. **Portfolio & Interview Pitch**: Exactly how to explain this project during a FAANG / top-tier technical interview.
"""
        return self._call_llm(prompt, system_instruction=system_instruction, temperature=0.4)

    def generate_career_roadmap(
        self, 
        career_path: str, 
        current_skills: str = "", 
        target_timeline_months: int = 6
    ) -> str:
        """Generate a complete skill tree, prerequisites, and milestone roadmap for a tech career path."""
        system_instruction = (
            "You are a Senior Tech Recruiter and Engineering Director. "
            "You design rigorous, hyper-focused career roadmaps that transform learners into job-ready engineers. "
            "Avoid fluff. Detail specific skill hierarchies, prerequisite milestones, portfolio projects, and interview tips."
        )

        skills_prompt = f"Learner's Current Skills: {current_skills}" if current_skills else "Starting from beginner / baseline."

        prompt = f"""
Design a master-level Career Roadmap for:
# 🎯 Target Role: "{career_path}"
Timeline Goal: {target_timeline_months} Months
{skills_prompt}

Structure your guidance as follows:
1. **Industry Reality & Role Archetype (2026/2027)**: What does a high-performing {career_path} actually do day-to-day?
2. **Prerequisites & Core Foundations**: What mathematical, CS, or logical foundations are non-negotiable?
3. **Structured Skill Tree**:
   - **Tier 1: Core Fundamentals**
   - **Tier 2: Production Tooling & Frameworks**
   - **Tier 3: Cloud, System Design & Architecture**
   - **Tier 4: Advanced Specializations & 2026 Trends**
4. **Milestone Learning Timeline (Month-by-Month)**: Actionable goals for Month 1, Month 2, Month 3-4, and Month 5-6.
5. **Top 3 Resume Capstone Projects**: Distinct projects that demonstrate real production competence over toy tutorials.
6. **Technical Interview Mastery Guide**: Core coding patterns, system design questions, and behavioural talking points.
"""
        return self._call_llm(prompt, system_instruction=system_instruction, temperature=0.4)

    # =========================================================================
    # FEATURE C: Context / Search Mode Toggle Tutor
    # =========================================================================

    def answer_tutor_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        search_mode: str,
        user_notes_context: str = "",
        max_search_results: int = 4
    ) -> Dict[str, Any]:
        """Context-aware tutor answering questions via either User Notes or Live Online Web Search.
        
        Args:
            query: The user's prompt or question.
            chat_history: Previous conversation turns [{'role': 'user'|'assistant', 'content': '...'}].
            search_mode: Either 'user_notes' (User Uploaded Resources) or 'online_search' (Online Web Search).
            user_notes_context: Combined clean Markdown text of user uploaded notes.
            max_search_results: Number of web results if online_search is active.
            
        Returns:
            Dict containing:
            - 'answer': str (formatted response)
            - 'mode': str
            - 'sources': List of sources (web links or note sections)
        """
        web_sources = []
        context_block = ""
        system_instruction = ""

        # Normalize search_mode string
        is_online = "online" in search_mode.lower() or "web" in search_mode.lower()

        if is_online:
            # Online Web Mode
            system_instruction = (
                "You are NoteNest's Real-Time AI Researcher. You ground your answers in both core CS wisdom "
                "and fresh, real-time live web search results. Cite your web sources directly using markdown links "
                "with the URLs provided. If information is evolving, state current industry consensus."
            )
            
            # Fetch live web results
            search_results = WebSearchEngine.search(query, max_results=max_search_results)
            web_sources = search_results
            formatted_search = WebSearchEngine.format_for_llm(search_results)
            
            context_block = f"""
{formatted_search}

Optional uploaded user notes context for reference:
{user_notes_context[:1500] if user_notes_context else "None provided."}
"""
        else:
            # User Notes Mode
            system_instruction = (
                "You are NoteNest's Strict Note Study Tutor. Your primary directive is to answer the user's questions "
                "STRICTLY using the information provided in their uploaded study notes, slides, and documents. "
                "Cite specific pages, slides, or sections from the notes whenever possible. "
                "If the user asks something NOT covered in their notes, explicitly inform them: "
                "'⚠️ Note Grounding: This specific detail is not present in your uploaded notes.' "
                "Then you may offer a brief general explanation while reminding them to verify with their course materials."
            )
            
            clean_notes = user_notes_context.strip() if user_notes_context else "NO USER NOTES UPLOADED YET."
            context_block = f"""
### 📄 UPLOADED USER NOTES CONTEXT:
{clean_notes}
"""

        # Format conversation history
        history_snippet = ""
        if chat_history:
            recent_turns = chat_history[-6:]
            history_lines = []
            for msg in recent_turns:
                role = "Student" if msg.get("role") == "user" else "Tutor"
                history_lines.append(f"{role}: {msg.get('content', '')}")
            history_snippet = "Recent Conversation History:\n" + "\n".join(history_lines) + "\n\n"

        full_prompt = f"""
{context_block}

{history_snippet}
Student Question: {query}

Please provide a clear, pedagogical, beautifully formatted response with code blocks, bullet points, and source citations where relevant:
"""
        answer_text = self._call_llm(full_prompt, system_instruction=system_instruction, temperature=0.35)

        return {
            "answer": answer_text,
            "mode": "online_search" if is_online else "user_notes",
            "sources": web_sources if is_online else [{"type": "user_notes", "title": "Uploaded Notes Context"}]
        }
