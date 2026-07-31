-- Migrate Clerk user reference to Supabase Auth user id (auth.users.id)

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'users'
      AND column_name = 'clerk_id'
  ) THEN
    ALTER TABLE users RENAME COLUMN clerk_id TO auth_user_id;
    DROP INDEX IF EXISTS idx_users_clerk_id;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_auth_user_id ON users (auth_user_id);

COMMENT ON COLUMN users.auth_user_id IS 'Supabase Auth user UUID (auth.users.id)';
