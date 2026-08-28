------------------------------------------------
--              ACL MANAGEMENT                --
------------------------------------------------
CREATE TABLE application.acl (
  "id" BIGSERIAL PRIMARY KEY,
  "role" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "resource" TEXT NOT NULL,
  "deny" BOOLEAN DEFAULT FALSE,
  "cdate" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  "origin" TEXT,
  UNIQUE("role", "action", "resource")
);

INSERT INTO
  application.acl (role, action, resource)
VALUES
  -- All users can access root
  (
    'trn:temboard:*:*:*',
    'GET:/',
    '*'
  ),
  -- All users can access login page
  (
    'trn:temboard:*:*:*',
    '*:/login',
    '*'
  ),
  -- All users can submit login form
  (
    'trn:temboard:*:*:*',
    '*:/json/login',
    '*'
  ),
  -- All users can access reset password page
  (
    'trn:temboard:*:*:*',
    '*:/reset-password',
    '*'
  ),
  -- All users can submit reset-password form
  (
    'trn:temboard:*:*:*',
    'POST:/json/reset-password',
    '*'
  ),
  -- All identified users can access logout
  (
    'trn:temboard:core:user:*',
    '*:/logout',
    '*'
  ),
  -- All identified users can access home
  (
    'trn:temboard:core:user:*',
    '*:/home',
    '*'
  ),
  -- All identified users can retrieve instances list
  (
    'trn:temboard:core:user:*',
    'GET:/json/instances/home',
    '*'
  ),
  -- All identified user can access about page
  (
    'trn:temboard:core:user:*',
    '*:/about',
    '*'
  ),
  -- All identified user can access explain page
  (
    'trn:temboard:core:user:*',
    '*:/explain',
    '*'
  ),
  -- All users from admins group have access to ALL requests
  (
    'trn:temboard:core:group:admins',
    '*',
    '*'
  ),
  -- ApiKey have access to open metrics
  (
    'trn:temboard:core:apikey:*',
    'GET:/proxy/<address>/<port>/monitoring/metrics',
    '*'
  );

-- Insert ACL for all existing dba groups
-- e.g. : mass/dba => "trn:temboard:core:group:mass/dba" "*" "trn:temboard:core:instance:mass"
INSERT INTO
  application.acl (role, action, resource)
SELECT
  'trn:temboard:core:group:' || g.name AS group,
  '*' AS action,
  'trn:temboard:core:instance:' || e.name AS instance
FROM
  application.groups g
  JOIN application.environments e ON g.id = e.dba_group_id;

-- Create group admins
INSERT INTO
  application.groups (name, description)
VALUES
  ('admins', 'Admin');

--Add every user having is_admin to true in admins group
INSERT INTO
  application.memberships (role_name, group_id)
SELECT
  r.role_name,
  (
    SELECT
      id
    FROM
      application.groups
    WHERE
      name = 'admins'
  )
FROM
  application.roles r
WHERE
  r.is_admin;