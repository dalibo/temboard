SELECT
  r.role_name,
  role_email,
  role_phone,
  is_active,
  is_admin,
  rxg.role_name AS group_role_name,  -- DEPRECATED: drop when using proper secondary table in SA.
  rxg.group_name,
  rxg.group_kind
FROM application.roles AS r
LEFT OUTER JOIN application.role_groups AS rxg ON rxg.role_name = r.role_name
WHERE r.role_name = :name;
