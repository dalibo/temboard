INSERT INTO application.roles (role_name, role_password)
VALUES (:name, :password)
RETURNING *;
