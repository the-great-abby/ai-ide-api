-- Add rule_proposals table
CREATE TABLE IF NOT EXISTS rule_proposals (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR DEFAULT 'pending',
    submitted_by VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback TEXT
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_rule_proposals_status ON rule_proposals(status);
CREATE INDEX IF NOT EXISTS idx_rule_proposals_submitted_by ON rule_proposals(submitted_by);
CREATE INDEX IF NOT EXISTS idx_rule_proposals_timestamp ON rule_proposals(timestamp); 