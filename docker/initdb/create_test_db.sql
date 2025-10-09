-- 02-create-test-db.sql (PostgreSQL)

-- Создать роль, если нет
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_user') THEN
    CREATE ROLE test_user LOGIN PASSWORD 'test_pass';
  END IF;
END $$;

-- Создать БД и назначить владельца
-- В Docker init скриптах можно использовать простую команду
CREATE DATABASE test_db OWNER test_user;

-- Разрешить подключение пользователю к БД (можно выполнять из любой БД)
GRANT CONNECT ON DATABASE test_db TO test_user;

-- Примечание: Дополнительные права внутри схем выполняйте в отдельном скрипте,
-- который подключается к test_db (например, 03-test-db-grants.sql с \connect test_db).
