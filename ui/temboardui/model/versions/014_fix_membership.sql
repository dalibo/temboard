------------------------------------------------
--     Fix role_name update propagation       --
------------------------------------------------

ALTER TABLE application.memberships
DROP CONSTRAINT memberships_role_name_fkey;

ALTER TABLE application.memberships
ADD CONSTRAINT memberships_role_name_fkey
FOREIGN KEY (role_name)
REFERENCES application.roles (role_name)
ON UPDATE CASCADE
ON DELETE CASCADE;
