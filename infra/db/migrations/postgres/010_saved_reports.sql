-- Server-side storage for saved recommendation reports (previously browser localStorage).
CREATE TABLE IF NOT EXISTS saved_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id TEXT NOT NULL,
    input JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_reports_owner_created
    ON saved_reports (auth_user_id, created_at DESC);
