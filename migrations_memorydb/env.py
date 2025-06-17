# env.py for memorydb migrations only
# This file is managed separately from the main migrations/env.py
# It uses the sqlalchemy.url from alembic_memorydb.ini

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# For memorydb, we do not use ORM autogenerate, only raw SQL migrations
# target_metadata = None

# Dynamically set the SQLAlchemy URL from environment variables
user = os.environ.get("POSTGRES_USER", "postgres")
password = os.environ.get("POSTGRES_PASSWORD", "postgres")
host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
db = os.environ.get("MEMORY_POSTGRES_DB", "memorydb")

SQLALCHEMY_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
context.config.set_main_option("sqlalchemy.url", SQLALCHEMY_URL)

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = os.environ.get("MEMORY_DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=None, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = os.environ.get("MEMORY_DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=None
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
