## ARR! UUIDs vs Strings for IDs and Foreign Keys

All ID columns and foreign keys in this codebase are `sa.String()` (VARCHAR), not native UUID. This be for maximum compatibility with SQLAlchemy, Alembic, and Postgres across all versions. If ye pass a `uuid.UUID` object to a query, cast it to `str()` first, or ye'll be walkin' the plank!

**Why?**
- Native UUID columns and FKs cause endless trouble with migrations, drivers, and test data.
- Mixing types (UUID in one table, String in another) is the path to madness and broken FKs.
- String columns work everywhere, but ye lose strict type safety.

**If ye ever want to switch to native UUIDs:**
- Ye must update *all* models, migrations, and test data at once, or face the wrath of broken foreign keys and migration errors.

See [`rules/db_types.mdc`](../../rules/db_types.mdc) for the full tale and best practices. 