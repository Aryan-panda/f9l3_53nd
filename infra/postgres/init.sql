-- ==============================================================================
-- f9l3_53nd PostgreSQL Initialization Script
-- ==============================================================================

-- Enable UUID extension for cryptographically unpredictable identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Notice logged during initialization
DO $$
BEGIN
    RAISE NOTICE 'f9l3_53nd database extensions initialized successfully.';
END
$$;
