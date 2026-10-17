"""Unit test for Gemma/Gemini Agent and Search Engine."""

import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from modules.gemma_agent import StudyCareerAgent
from modules.search_engine import WebSearchEngine

def test_search_engine():
    print("Testing WebSearchEngine...")
    results = WebSearchEngine.search("python fast api documentation", max_results=2)
    print(f"WebSearchEngine results count: {len(results)}")
    assert len(results) > 0, "Expected at least 1 search result"
    print("Sample result title:", results[0]["title"])
    formatted = WebSearchEngine.format_for_llm(results)
    assert "Live Web Search Results" in formatted
    print("PASS: WebSearchEngine is operational! ✅")

def test_agent_initialization():
    print("\nTesting StudyCareerAgent initialization...")
    agent = StudyCareerAgent()
    print("Agent is_configured:", agent.is_configured)
    assert agent.is_configured, "Agent should be configured with GOOGLE_API_KEY"
    
    # Quick generation test
    sample_notes = """
    # Python GIL & Concurrency
    The Global Interpreter Lock is a mutex in CPython.
    Multiprocessing creates separate processes with dedicated memory heaps.
    Asyncio is single-threaded cooperative multitasking.
    """
    
    print("\nTesting generate_flashcards...")
    cards, csv_text = agent.generate_flashcards(sample_notes, card_count=3)
    print(f"Generated {len(cards)} cards:")
    for c in cards:
        print(f" - Front: {c['front']}\n   Back: {c['back']}")
    assert len(cards) >= 1
    assert "Front,Back" in csv_text or len(csv_text) > 10
    print("PASS: Flashcards & Anki CSV generation passed! ✅")

if __name__ == "__main__":
    test_search_engine()
    test_agent_initialization()
