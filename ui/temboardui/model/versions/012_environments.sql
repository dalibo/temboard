------------------------------------------------
-- Migrating instance groups to environments. --
------------------------------------------------

CREATE TABLE application.environments (
	id SERIAL PRIMARY KEY,
	name TEXT UNIQUE NOT NULL,
	description TEXT,
	color TEXT,
	cdate TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Migrate instance groups to environments.
INSERT INTO application.environments (name, description)
-- Create an environment per group combination.
-- An instance in two groups will create a single environment combining both.
SELECT DISTINCT
	string_agg(DISTINCT ixg.group_name, '-' ORDER BY ixg.group_name) AS name,
	string_agg(DISTINCT g.group_description, ' / ') AS description
  FROM application.instances AS i
  JOIN application.instance_groups AS ixg
    ON i.agent_address = ixg.agent_address
   AND i.agent_port = ixg.agent_port
   AND ixg.group_kind = 'instance'
  JOIN application.groups AS g
    ON ixg.group_kind = g.group_kind
   AND ixg.group_name = g.group_name
 GROUP BY i.agent_address, i.agent_port

 UNION

-- Create an environment per empty group.
SELECT DISTINCT g.group_name AS name, g.group_description AS description
  FROM application.groups AS g
  LEFT OUTER JOIN application.instance_groups
    ON instance_groups.group_kind = g.group_kind
   AND instance_groups.group_name = g.group_name
 WHERE g.group_kind = 'instance'
   AND instance_groups.agent_address IS NULL

 UNION

SELECT DISTINCT
	'temboard-noenv-fallback' AS name,
	'Fallback environment for instances without group' AS description
  FROM application.instances AS i
  LEFT OUTER JOIN application.instance_groups AS ixg
    ON i.agent_address = ixg.agent_address AND i.agent_port = ixg.agent_port
   AND ixg.group_kind = 'instance'
 WHERE ixg.agent_address IS NULL

 ORDER BY 1
;

-- Associate instance to one single environment.
ALTER TABLE application.instances
  ADD COLUMN environment_id INTEGER REFERENCES application.environments(id);

CREATE VIEW application.vinstances AS
SELECT
	i.agent_address || ':' || i.agent_port AS agent,
	hostname || ':' || pg_port AS postgres,
	e.name AS environment_name,
	array_agg(p.plugin_name ORDER BY p.plugin_name) FILTER (WHERE p.plugin_name IS NOT NULL) AS plugins
  FROM application.instances AS i
  JOIN application.environments AS e
    ON i.environment_id = e.id
  LEFT OUTER JOIN application.plugins AS p ON p.agent_address = i.agent_address AND p.agent_port = i.agent_port
 GROUP BY 1, 2, 3;

-- Attach instance to corresponding environment.
WITH mapping AS (
	SELECT DISTINCT
		i.agent_address AS agent_address,
		i.agent_port AS agent_port,
		string_agg(DISTINCT ixg.group_name, '-' ORDER BY ixg.group_name) AS environment_name
	  FROM application.instances AS i
	  JOIN application.instance_groups AS ixg
	    ON i.agent_address = ixg.agent_address AND i.agent_port = ixg.agent_port
	   AND ixg.group_kind = 'instance'
	  JOIN application.groups AS g
	    ON ixg.group_kind = g.group_kind AND ixg.group_name = g.group_name
	 GROUP BY i.agent_address, i.agent_port
)
UPDATE application.instances AS i
   SET environment_id = e.id
  FROM mapping
  JOIN application.environments AS e ON e.name = mapping.environment_name
 WHERE i.agent_address = mapping.agent_address
   AND i.agent_port = mapping.agent_port;

UPDATE application.instances
   SET environment_id = (SELECT id FROM application.environments WHERE name = 'temboard-noenv-fallback')
 WHERE environment_id IS NULL;

ALTER TABLE application.instances
ALTER COLUMN environment_id SET NOT NULL;

--------------------------------------------
-- Migrating role groups to environments. --
--------------------------------------------

ALTER TABLE application.groups RENAME TO legacy_groups;

-- New groups table without kind, and with an integer primary key.
CREATE TABLE application.groups (
	id SERIAL PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	description TEXT,
	cdate TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
ALTER TABLE application.environments
  ADD COLUMN dba_group_id INTEGER REFERENCES application.groups(id) ON DELETE CASCADE;

-- Use a secondary table to link group to their role members.
-- Replaces application.role_groups.
CREATE TABLE application.memberships (
	id SERIAL PRIMARY KEY,
	role_name TEXT NOT NULL REFERENCES application.roles(role_name) ON DELETE CASCADE,
	group_id INTEGER NOT NULL REFERENCES application.groups(id) ON DELETE CASCADE,
	cdate TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
	UNIQUE (role_name, group_id)
);

CREATE VIEW application.vroles AS
SELECT
	r.role_name AS role,
	r.is_active AS active,
	r.is_admin AS admin,
	array_agg(DISTINCT g.name ORDER BY g.name) FILTER (WHERE g.name IS NOT NULL) AS groups
  FROM application.roles AS r
  LEFT OUTER JOIN application.memberships AS m
    ON r.role_name = m.role_name
  LEFT OUTER JOIN application.groups AS g
    ON m.group_id = g.id
 GROUP BY 1, 2, 3
 ORDER BY 1
;

-- Create a */dba group for each environment.
INSERT INTO application.groups (name, description)
SELECT DISTINCT
	e.name || '/dba' AS name,
	-- Profile description in /settings/environments/EEE/members
	'DBA' AS description
  FROM application.environments AS e
 ORDER BY 1;

-- Assign the */dba group to the corresponding environment.
UPDATE application.environments AS e
   SET dba_group_id = g.id
  FROM application.groups AS g
 WHERE g.name = e.name || '/dba';

ALTER TABLE application.environments
ALTER COLUMN dba_group_id SET NOT NULL;

-- Migrate membership from legacy role_groups.
WITH legacy AS (
    -- List all role belonging to a DBA groups.
	SELECT DISTINCT
		rxg.role_name,
		e.dba_group_id
	-- instance_groups has no entry for empty environments.
	-- We'll handle this later.
	  FROM application.instances AS i
	  JOIN application.environments AS e ON e.id = i.environment_id
	  JOIN application.instance_groups AS ixg ON ixg.agent_address = i.agent_address AND ixg.agent_port = i.agent_port
	  JOIN application.access_role_instance AS ari
	    ON ari.instance_group_name = ixg.group_name
	   AND ari.instance_group_kind = ixg.group_kind
	  JOIN application.role_groups AS rxg
	    ON rxg.group_name = ari.role_group_name
	   AND rxg.group_kind = ari.role_group_kind
)
INSERT INTO application.memberships (role_name, group_id)
SELECT role_name, dba_group_id FROM legacy

 UNION

-- Create a membership for each empty environments.
SELECT DISTINCT
	rxg.role_name,
	e.dba_group_id
  FROM application.legacy_groups AS ig
  JOIN application.environments AS e
    ON e.name = ig.group_name
   AND ig.group_kind = 'instance'
  JOIN application.access_role_instance AS ari
    ON ari.instance_group_name = ig.group_name
   AND ari.instance_group_kind = ig.group_kind
  JOIN application.role_groups AS rxg
    ON rxg.group_name = ari.role_group_name
   AND rxg.group_kind = ari.role_group_kind
  LEFT OUTER JOIN application.instance_groups AS ixg
	ON ixg.group_name = ig.group_name
   AND ixg.group_kind = ig.group_kind
 WHERE ixg.group_name IS NULL AND ixg.group_kind IS NULL

 ORDER BY 1, 2
;


DROP TABLE application.instance_groups;
DROP TABLE application.access_role_instance;
DROP TABLE application.role_groups;
DROP TABLE application.legacy_groups;
