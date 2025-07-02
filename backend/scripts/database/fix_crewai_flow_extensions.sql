-- Fix crewai_flow_state_extensions table for flow coordination
-- Add missing columns and drop discovery_flow_id

BEGIN;

-- Add missing columns for flow coordination
ALTER TABLE crewai_flow_state_extensions 
ADD COLUMN IF NOT EXISTS client_account_id UUID NOT NULL DEFAULT '11111111-1111-1111-1111-111111111111',
ADD COLUMN IF NOT EXISTS engagement_id UUID NOT NULL DEFAULT '22222222-2222-2222-2222-222222222222',
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255) NOT NULL DEFAULT 'system',
ADD COLUMN IF NOT EXISTS flow_type VARCHAR(50) NOT NULL DEFAULT 'discovery',
ADD COLUMN IF NOT EXISTS flow_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS flow_status VARCHAR(50) NOT NULL DEFAULT 'initialized',
ADD COLUMN IF NOT EXISTS flow_configuration JSONB NOT NULL DEFAULT '{}';

-- Add unique constraint on flow_id if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'crewai_flow_state_extensions_flow_id_key'
    ) THEN
        ALTER TABLE crewai_flow_state_extensions 
        ADD CONSTRAINT crewai_flow_state_extensions_flow_id_key UNIQUE (flow_id);
    END IF;
END $$;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_crewai_flow_extensions_client_account 
ON crewai_flow_state_extensions(client_account_id);

CREATE INDEX IF NOT EXISTS idx_crewai_flow_extensions_engagement 
ON crewai_flow_state_extensions(engagement_id);

CREATE INDEX IF NOT EXISTS idx_crewai_flow_extensions_flow_type 
ON crewai_flow_state_extensions(flow_type);

-- Drop discovery_flow_id column (no longer needed)
ALTER TABLE crewai_flow_state_extensions 
DROP COLUMN IF EXISTS discovery_flow_id;

-- Update existing records with demo values
UPDATE crewai_flow_state_extensions 
SET 
    flow_name = COALESCE(flow_name, 'Legacy Flow ' || SUBSTRING(flow_id::text, 1, 8)),
    flow_type = COALESCE(flow_type, 'discovery'),
    flow_status = COALESCE(flow_status, 'initialized')
WHERE flow_name IS NULL OR flow_type IS NULL OR flow_status IS NULL;

COMMIT;

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default 
FROM information_schema.columns 
WHERE table_name = 'crewai_flow_state_extensions' 
ORDER BY ordinal_position;