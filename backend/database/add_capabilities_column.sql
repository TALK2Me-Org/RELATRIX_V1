-- Migration to add capabilities column to agents table
-- This column was missing from the original schema but is required by the code

ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS capabilities JSONB DEFAULT '[]'::jsonb;

-- Update the comment to explain the column
COMMENT ON COLUMN agents.capabilities IS 'JSON array of agent capabilities/features';