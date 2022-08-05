INSERT INTO "application"."apikeys"("secret", "comment")
VALUES (:secret, :comment)
RETURNING *;
