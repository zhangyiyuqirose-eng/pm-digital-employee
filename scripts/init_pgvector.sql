-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pm_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pm_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized successfully';
END $$;