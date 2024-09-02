SELECT
    e.id AS e_id,
    e.name AS e_name,
    e.description AS e_description,
    e.color,
    e.dba_group_id,
    g.id AS g_id,
    g.name AS g_name,
    g.description AS g_description
  FROM application.environments AS e
  JOIN application.groups AS g ON g.id = e.dba_group_id
 WHERE e.name = :name
