DROP SCHEMA "public";

\echo ---------------------------------
\echo --
\echo -- Adding some users and groups
\echo --
\echo ---------------------------------
\echo


INSERT INTO application.roles (role_name, role_password, role_email, is_active, is_admin)
VALUES
-- alice // alice
('alice', 'Xm4iJH8aQmXRvrsLy/fNbQU23K6/FlEVRhhPZKO2aHvYVGzCft+u7RXQ9Z48IyVtnS+n47UM3QUM4is0BVTPOA==', 'alice@temboard.local', true, false),
-- bob // bob
('bob', 'f9Yol14q9N89EyYSCUR9izXfXugNiXN/HiKsa8CFnIzq/MADFgL7UnjMnxBVypSP6vzPbusotyEAF5H6tP2Mlw==', 'bob@temboard.local', true, false);

INSERT INTO application.groups (name, description)
VALUES
('mass/dba', 'DBA'),
('stable/dba', 'DBA');

INSERT INTO application.environments (name, description, dba_group_id)
VALUES
('stable', 'Agent of previous major version of temBoard', (SELECT id FROM application.groups WHERE name = 'stable/dba')),
('mass', 'Big herd of instances.', (SELECT id FROM application.groups WHERE name = 'mass/dba'));

INSERT INTO application.memberships (role_name, group_id)
VALUES
('alice', (SELECT id FROM application.groups WHERE name = 'default/dba')),
('alice', (SELECT id FROM application.groups WHERE name = 'stable/dba')),
('bob', (SELECT id FROM application.groups WHERE name = 'default/dba')),
('admin', (SELECT id FROM application.groups WHERE name = 'stable/dba')),
('admin', (SELECT id FROM application.groups WHERE name = 'mass/dba'));

-- Pre-register agents

INSERT INTO application.instances
(agent_address, agent_port, hostname, pg_port, comment, notify, environment_id)
VALUES
('0.0.0.0', 2347, 'postgres-stable.dev', 5432, '', FALSE, (SELECT id FROM application.environments WHERE name = 'stable')),
('0.0.0.0', 2345, 'postgres0.dev', 5432, '', FALSE, (SELECT id FROM application.environments WHERE name = 'default')),
('0.0.0.0', 2346, 'postgres1.dev', 5432, '', FALSE, (SELECT id FROM application.environments WHERE name = 'default'));

INSERT INTO application.plugins
(agent_address, agent_port, plugin_name)
VALUES
('0.0.0.0', 2345, 'dashboard'),
('0.0.0.0', 2345, 'pgconf'),
('0.0.0.0', 2345, 'activity'),
('0.0.0.0', 2345, 'monitoring'),
('0.0.0.0', 2345, 'maintenance'),
('0.0.0.0', 2345, 'statements'),
('0.0.0.0', 2346, 'dashboard'),
('0.0.0.0', 2346, 'pgconf'),
('0.0.0.0', 2346, 'activity'),
('0.0.0.0', 2346, 'monitoring'),
('0.0.0.0', 2346, 'maintenance'),
('0.0.0.0', 2346, 'statements'),
('0.0.0.0', 2347, 'dashboard'),
('0.0.0.0', 2347, 'pgconf'),
('0.0.0.0', 2347, 'activity'),
('0.0.0.0', 2347, 'monitoring'),
('0.0.0.0', 2347, 'maintenance'),
('0.0.0.0', 2347, 'statements');

-- Insert a predictable API key for preconfigured prometheus and other
-- development purpose. See dev/prometheus/prometheus.yml.
INSERT INTO application.apikeys
(secret, comment)
VALUES
('UNSECURE_DEV_APIKEY', 'Created by dev-fixture.sql');
