# Graph Report - NoteNest  (2026-10-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 103 nodes · 164 edges · 11 communities (3 shown, 8 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.91)
- Token cost: 680 input · 88 output

## Graph Freshness
- Built from commit: `873a336b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AI Agent Core
- Document Parsing Engine
- Test Document Generation
- Web Search Integration
- Project Dependencies
- Streamlit Web Application

## God Nodes (most connected - your core abstractions)
1. `StudyCareerAgent` - 17 edges
2. `DocumentIngestor` - 10 edges
3. `WebSearchEngine` - 10 edges
4. `DocumentResult` - 7 edges
5. `Repository` - 7 edges
6. `test_agent_initialization()` - 4 edges
7. `test_search_engine()` - 4 edges
8. `test_ingestion()` - 3 edges
9. `create_sample_docx()` - 3 edges
10. `create_sample_pdf()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `get_agent()` --uses--> `StudyCareerAgent`  [INFERRED]
  app.py → modules/gemma_agent.py
- `test_ingestion()` --uses--> `DocumentIngestor`  [INFERRED]
  tests/test_ingestor.py → modules/ingestor.py
- `test_search_engine()` --uses--> `WebSearchEngine`  [INFERRED]
  tests/test_agent.py → modules/search_engine.py
- `StudyCareerAgent` --uses--> `WebSearchEngine`  [INFERRED]
  modules/gemma_agent.py → modules/search_engine.py
- `test_agent_initialization()` --calls--> `StudyCareerAgent`  [EXTRACTED]
  tests/test_agent.py → modules/gemma_agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Document Ingestion & Parsing Stack** — requirements_pymupdf, requirements_python_pptx [EXTRACTED 1.00]
- **Knowledge Graph & Analytics Stack** — requirements_graphifyy, requirements_networkx [EXTRACTED 1.00]

## Communities (11 total, 8 thin omitted)

### Community 1 - "Document Parsing Engine"
Cohesion: 0.25
Nodes (3): DocumentIngestor, DocumentResult, test_ingestion()

### Community 2 - "Test Document Generation"
Cohesion: 0.20
Nodes (3): create_sample_docx(), create_sample_pdf(), create_sample_pptx()

### Community 4 - "Project Dependencies"
Cohesion: 0.25
Nodes (8): Repository, google-generativeai, graphifyy, networkx, PyMuPDF, python-dotenv, python-pptx, streamlit

## Knowledge Gaps
- **7 isolated node(s):** `google-generativeai`, `graphifyy`, `networkx`, `PyMuPDF`, `python-dotenv` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 55 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `StudyCareerAgent` connect `AI Agent Core` to `Unit Testing Suite`, `Web Search Integration`, `Streamlit Web Application`, `Agent Configuration`?**
  _High betweenness centrality (0.339) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `StudyCareerAgent` (e.g. with `get_agent()` and `WebSearchEngine`) actually correct?**
  _`StudyCareerAgent` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `google-generativeai`, `graphifyy`, `networkx` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AI Agent Core` be split into smaller, more focused modules?**
  _Cohesion score 0.12121212121212122 - nodes in this community are weakly interconnected._
- **Why does `DocumentIngestor` connect `Document Parsing Engine` to `Unit Testing Suite`, `Streamlit Web Application`, `Document Ingestion Utilities`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `WebSearchEngine` (e.g. with `StudyCareerAgent` and `test_search_engine()`) actually correct?**
  _`WebSearchEngine` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `WebSearchEngine` connect `Web Search Integration` to `AI Agent Core`, `Streamlit Web Application`, `Agent Configuration`, `Search Engine Implementation`, `Unit Testing Suite`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._