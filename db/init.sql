-- Runs once, on first start of the PostgreSQL container.
-- pgvector powers the legal knowledge base (table `kb_chunks`, created by the AI service).
-- The relational schema (users, documents, results, deadlines) is created by the backend via Flyway.
CREATE EXTENSION IF NOT EXISTS vector;
