DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statusenum') THEN
        DROP TYPE statusenum;
    END IF;
END
$$; 