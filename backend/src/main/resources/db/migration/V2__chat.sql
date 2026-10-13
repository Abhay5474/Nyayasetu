-- One continuous Q&A conversation per document.
CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY,
    document_id UUID        NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    user_id     UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role        VARCHAR(10) NOT NULL,
    language    VARCHAR(5)  NOT NULL,
    content     TEXT        NOT NULL,
    details     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX chat_messages_doc_created_idx ON chat_messages (document_id, created_at);
