SELECT
  e.id,
  e.name,
  e.description,
  e.color
  e.cdate,
  e.dba_group_id
FROM application.environment AS e
WHERE e.name = :name;
