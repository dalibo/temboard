SELECT
  id, secret, comment, cdate, edate
FROM "application"."apikeys"
WHERE "edate" > NOW();
