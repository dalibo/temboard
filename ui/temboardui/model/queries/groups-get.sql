SELECT
  group_name, group_kind, group_description
FROM application.groups
WHERE group_kind = :kind AND group_name = :name;
