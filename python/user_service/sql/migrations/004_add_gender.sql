-- Пол как PostgreSQL ENUM (не VARCHAR).
DO $$ BEGIN
    CREATE TYPE gender AS ENUM ('male', 'female');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'users'
          AND column_name = 'gender'
    ) THEN
        ALTER TABLE users
            ADD COLUMN gender gender NOT NULL DEFAULT 'male';
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'users'
          AND column_name = 'gender'
          AND udt_name IN ('varchar', 'text', 'bpchar')
    ) THEN
        ALTER TABLE users ALTER COLUMN gender DROP DEFAULT;
        ALTER TABLE users
            ALTER COLUMN gender TYPE gender
            USING (
                CASE
                    WHEN gender::text IN ('male', 'female') THEN gender::text::gender
                    ELSE 'male'::gender
                END
            );
        ALTER TABLE users ALTER COLUMN gender SET DEFAULT 'male'::gender;
        ALTER TABLE users ALTER COLUMN gender SET NOT NULL;
    END IF;
END $$;
