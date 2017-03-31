\echo ---------------------------------
\echo --
\echo -- Adding some users and groups
\echo --
\echo ---------------------------------
\echo

INSERT INTO application.groups (group_name, group_description, group_kind)
VALUES ('admins', 'The administrators', 'role'),
       ('users', 'The users', 'role');

INSERT INTO application.roles (role_name, role_password, role_email, is_active, is_admin)
-- alice // alice
VALUES ('alice', 'Xm4iJH8aQmXRvrsLy/fNbQU23K6/FlEVRhhPZKO2aHvYVGzCft+u7RXQ9Z48IyVtnS+n47UM3QUM4is0BVTPOA==', 'alice@temboard.local', true, false),
-- bob // bob
       ('bob', 'f9Yol14q9N89EyYSCUR9izXfXugNiXN/HiKsa8CFnIzq/MADFgL7UnjMnxBVypSP6vzPbusotyEAF5H6tP2Mlw==', 'bob@temboard.local', true, false);

INSERT INTO application.role_groups (role_name, group_name, group_kind)
VALUES ('admin', 'admins', 'role'),
       ('alice', 'users', 'role'),
       ('bob',   'users', 'role');

INSERT INTO application.groups (group_name, group_description, group_kind)
VALUES ('local_instances', 'The local instances', 'instance');

INSERT INTO application.access_role_instance(role_group_name, role_group_kind, instance_group_name, instance_group_kind)
VALUES ('admins', 'role', 'local_instances', 'instance'),
       ('users',  'role', 'local_instances', 'instance');
