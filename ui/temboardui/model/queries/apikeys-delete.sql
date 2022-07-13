DELETE FROM "application"."apikeys"
WHERE "id" = :id
RETURNING "id", "comment";
