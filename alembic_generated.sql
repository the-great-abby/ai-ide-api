BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_create_feedback

DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback') THEN DROP TYPE feedback; END IF; END $$;;

CREATE TABLE feedback (
    id VARCHAR NOT NULL, 
    rule_id VARCHAR, 
    project VARCHAR, 
    feedback_type VARCHAR, 
    comment TEXT, 
    submitted_by VARCHAR, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_feedback_id ON feedback (id);

CREATE INDEX ix_feedback_project ON feedback (project);

CREATE INDEX ix_feedback_rule_id ON feedback (rule_id);

CREATE INDEX ix_feedback_submitted_by ON feedback (submitted_by);

INSERT INTO alembic_version (version_num) VALUES ('0001_create_feedback') RETURNING alembic_version.version_num;

-- Running upgrade 0001_create_feedback -> 0002_create_proposals

CREATE TABLE proposals (
    id VARCHAR NOT NULL, 
    rule_type VARCHAR, 
    description TEXT, 
    diff TEXT, 
    status VARCHAR, 
    submitted_by VARCHAR, 
    project VARCHAR, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    version INTEGER, 
    categories VARCHAR, 
    tags VARCHAR, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_proposals_id ON proposals (id);

CREATE INDEX ix_proposals_project ON proposals (project);

CREATE INDEX ix_proposals_rule_type ON proposals (rule_type);

CREATE INDEX ix_proposals_submitted_by ON proposals (submitted_by);

UPDATE alembic_version SET version_num='0002_create_proposals' WHERE alembic_version.version_num = '0001_create_feedback';

-- Running upgrade 0002_create_proposals -> 0003_create_rule_versions

CREATE TABLE rule_versions (
    id VARCHAR NOT NULL, 
    rule_id VARCHAR, 
    version INTEGER, 
    rule_type VARCHAR, 
    description TEXT, 
    diff TEXT, 
    status VARCHAR, 
    submitted_by VARCHAR, 
    added_by VARCHAR, 
    project VARCHAR, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    categories VARCHAR, 
    tags VARCHAR, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_rule_versions_id ON rule_versions (id);

CREATE INDEX ix_rule_versions_rule_id ON rule_versions (rule_id);

UPDATE alembic_version SET version_num='0003_create_rule_versions' WHERE alembic_version.version_num = '0002_create_proposals';

-- Running upgrade 0003_create_rule_versions -> 0004_create_rules

CREATE TABLE rules (
    id VARCHAR NOT NULL, 
    rule_type VARCHAR, 
    description TEXT, 
    diff TEXT, 
    status VARCHAR, 
    submitted_by VARCHAR, 
    added_by VARCHAR, 
    project VARCHAR, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    version INTEGER, 
    categories VARCHAR, 
    tags VARCHAR, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_rules_added_by ON rules (added_by);

CREATE INDEX ix_rules_id ON rules (id);

CREATE INDEX ix_rules_project ON rules (project);

CREATE INDEX ix_rules_rule_type ON rules (rule_type);

CREATE INDEX ix_rules_submitted_by ON rules (submitted_by);

UPDATE alembic_version SET version_num='0004_create_rules' WHERE alembic_version.version_num = '0003_create_rule_versions';

-- Running upgrade 0004_create_rules -> 0005_debug_side_effect

CREATE TABLE debug_side_effect (
    id SERIAL NOT NULL, 
    message VARCHAR(255) NOT NULL, 
    PRIMARY KEY (id)
);

INSERT INTO debug_side_effect (message) VALUES ('debug migration ran');

UPDATE alembic_version SET version_num='0005_debug_side_effect' WHERE alembic_version.version_num = '0004_create_rules';

-- Running upgrade 0005_debug_side_effect -> 20240603_alter_alembic_version_num_length

ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);;

UPDATE alembic_version SET version_num='20240603_alter_alembic_version_num_length' WHERE alembic_version.version_num = '0005_debug_side_effect';

COMMIT;

