\echo ---------------------------------
\echo --
\echo -- Adding some users and groups
\echo --
\echo ---------------------------------
\echo

INSERT INTO application.roles (role_name, role_password, role_email, is_active, is_admin)
-- alice // alice
VALUES ('alice', 'Xm4iJH8aQmXRvrsLy/fNbQU23K6/FlEVRhhPZKO2aHvYVGzCft+u7RXQ9Z48IyVtnS+n47UM3QUM4is0BVTPOA==', 'alice@temboard.local', true, false),
-- bob // bob
       ('bob', 'f9Yol14q9N89EyYSCUR9izXfXugNiXN/HiKsa8CFnIzq/MADFgL7UnjMnxBVypSP6vzPbusotyEAF5H6tP2Mlw==', 'bob@temboard.local', true, false);

INSERT INTO application.role_groups (role_name, group_name, group_kind)
VALUES ('alice', 'default', 'role'),
       ('bob', 'default', 'role');
