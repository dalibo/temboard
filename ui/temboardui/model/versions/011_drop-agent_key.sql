BEGIN;

ALTER TABLE application.instances DROP COLUMN IF EXISTS agent_key;

COMMIT;
