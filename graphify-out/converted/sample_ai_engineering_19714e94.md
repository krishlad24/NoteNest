<!-- converted from sample_ai_engineering.docx -->

AI Engineering & Production LLM Architecture
# 1. Retrieval Augmented Generation (RAG) Fundamentals
Retrieval Augmented Generation (RAG) optimizes the output of large language models by referencing an authoritative knowledge base outside of its training data before generating a response.
- Key architectural stages include:
- Document Chunking: Splitting source text with recursive character splitting or semantic boundary detection.
- Vector Embedding: Generating dense vector embeddings using models such as text-embedding-3 or nomic-embed.
- Indexing & Search: Storing vectors in HNSW / IVF indexes (e.g., Pinecone, Chroma, Milvus, pgvector).
- Re-ranking & Synthesis: Employing cross-encoders (e.g. BGE-Reranker) before prompt injection.
# 2. Core Latency & Cost Trade-offs
| Approach | Context Window / Latency | Cost & Accuracy Impact |
| --- | --- | --- |
| Naive RAG (Top-5 chunks) | Low Latency (~300ms) | Very Cost-Effective, Risk of missing context |
| Reranked Hybrid Search | Moderate Latency (~600ms) | Optimal Balance, ~92% answer accuracy |
| Full-Context Ingestion | High Latency (2s - 8s) | High Token Cost, needle-in-haystack degradation |
# 3. Best Practices for Production Deployment
Implement continuous eval harnesses (e.g. Ragas, TruLens) measuring Context Relevance, Faithfulness, and Answer Relevance. Cache recurring prompts using semantic redis caching.