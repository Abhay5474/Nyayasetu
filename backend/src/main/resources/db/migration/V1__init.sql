-- NyayaSetu relational schema. (The pgvector knowledge base `kb_chunks` is owned by the AI service.)

CREATE TABLE users (
    id                  UUID PRIMARY KEY,
    email               VARCHAR(255) NOT NULL,
    password_hash       VARCHAR(100) NOT NULL,
    full_name           VARCHAR(120) NOT NULL,
    phone               VARCHAR(20),
    role                VARCHAR(20)  NOT NULL DEFAULT 'USER',
    preferred_language  VARCHAR(5)   NOT NULL DEFAULT 'en',
    email_alerts        BOOLEAN      NOT NULL DEFAULT TRUE,
    sms_alerts          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX users_email_uq ON users (lower(email));

CREATE TABLE documents (
    id                 UUID PRIMARY KEY,
    user_id            UUID         NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    original_filename  VARCHAR(255) NOT NULL,
    stored_path        VARCHAR(300) NOT NULL,
    content_type       VARCHAR(100) NOT NULL,
    size_bytes         BIGINT       NOT NULL,
    sha256             VARCHAR(64)  NOT NULL,
    status             VARCHAR(20)  NOT NULL,
    error_message      TEXT,
    page_count         INTEGER,
    extraction_method  VARCHAR(10),
    detected_language  VARCHAR(10),
    extracted_text     TEXT,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX documents_user_created_idx ON documents (user_id, created_at DESC);

CREATE TABLE processing_results (
    id            UUID PRIMARY KEY,
    document_id   UUID        NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    language      VARCHAR(5)  NOT NULL,
    status        VARCHAR(20) NOT NULL,
    result        JSONB,
    model         VARCHAR(100),
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT processing_results_doc_lang_uq UNIQUE (document_id, language)
);

CREATE TABLE deadlines (
    id                  UUID PRIMARY KEY,
    document_id         UUID        NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    user_id             UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    description         TEXT        NOT NULL,
    due_date            DATE,
    period_text         TEXT,
    source_text         TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    last_reminder_stage INTEGER,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX deadlines_user_due_idx ON deadlines (user_id, due_date);
CREATE INDEX deadlines_due_pending_idx ON deadlines (due_date) WHERE status = 'PENDING';
CREATE INDEX deadlines_document_idx ON deadlines (document_id);

CREATE TABLE notification_log (
    id          UUID PRIMARY KEY,
    deadline_id UUID        NOT NULL REFERENCES deadlines (id) ON DELETE CASCADE,
    channel     VARCHAR(10) NOT NULL,
    success     BOOLEAN     NOT NULL,
    detail      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
