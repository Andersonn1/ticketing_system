CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE user_role AS ENUM ('STUDENT', 'FACULTY', 'ALUM', 'VENDOR', 'OTHER');
CREATE TYPE service_status AS ENUM ('OPEN', 'PENDING', 'CLOSED');
CREATE TYPE service_priority AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE service_category AS ENUM ('HARDWARE', 'SOFTWARE', 'NETWORK', 'SECURITY', 'OTHER');
CREATE TYPE ai_confidence AS ENUM ('HIGH', 'MEDIUM', 'LOW');

CREATE TABLE IF NOT EXISTS ticket (
    id BIGSERIAL PRIMARY KEY,
    requestor_name TEXT NOT NULL,
    requestor_email TEXT NOT NULL,
    user_role user_role NOT NULL DEFAULT 'OTHER',
    title VARCHAR(125) NOT NULL,
    description TEXT NOT NULL,
    status service_status NOT NULL DEFAULT 'OPEN',
    priority service_priority NOT NULL DEFAULT 'LOW',
    category service_category NOT NULL DEFAULT 'OTHER',
    ai_summary TEXT,
    ai_response TEXT,
    ai_next_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_confidence ai_confidence,
    ai_trace JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_chunk (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ticket_embedding (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
    combined_text TEXT NOT NULL,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_ticket_status ON ticket(status);
CREATE INDEX IF NOT EXISTS idx_ticket_category ON ticket(category);

CREATE INDEX IF NOT EXISTS idx_kb_chunk_embedding
ON kb_chunk
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

CREATE INDEX IF NOT EXISTS idx_ticket_embedding_embedding
ON ticket_embedding
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
