DELETE FROM "application"."apikeys"
WHERE "edate" < NOW()
RETURNING "id", "comment";
