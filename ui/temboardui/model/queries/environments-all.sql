SELECT
    e.id,
    e.name,
    e.description,
    e.color,
    e.dba_group_id,
    g.id AS g_id,
    g.name AS g_name,
    g.description AS g_description
  FROM application.environments AS e
  JOIN application.groups AS g ON g.id = e.dba_group_id
 ORDER BY 2
