from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import BLOB
from datetime import datetime
import enum
import uuid
import os

# SQLite database URL
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "rulesdb")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "db-test")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum for rule/proposal/feedback status
class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    reverted_to_enhancement = "reverted_to_enhancement"  # New status

# Rule model
class Rule(Base):
    __tablename__ = "rules"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_type = Column(String, index=True)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.approved)
    submitted_by = Column(String, index=True)
    added_by = Column(String, index=True, nullable=True)
    project = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    categories = Column(String, default="")  # Comma-separated
    tags = Column(String, default="")        # Comma-separated
    examples = Column(Text, nullable=True, default=None)

# Proposal model
class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, nullable=True)  # New: reference to rule being updated
    rule_type = Column(String, index=True)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    submitted_by = Column(String, index=True)
    project = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    categories = Column(String, default="")  # Comma-separated
    tags = Column(String, default="")        # Comma-separated
    examples = Column(Text, nullable=True, default=None)

# Feedback model
class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, index=True)
    project = Column(String, index=True, nullable=True)
    feedback_type = Column(String)
    comment = Column(Text, nullable=True)
    submitted_by = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# RuleVersion model for version history
class RuleVersion(Base):
    __tablename__ = "rule_versions"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, index=True)
    version = Column(Integer)
    rule_type = Column(String)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum))
    submitted_by = Column(String)
    added_by = Column(String, nullable=True)
    project = Column(String, nullable=True)
    timestamp = Column(DateTime)
    categories = Column(String, default="")
    tags = Column(String, default="")
    examples = Column(Text, nullable=True, default=None)

# BugReport model for bug reporting
class BugReport(Base):
    __tablename__ = "bug_reports"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    description = Column(Text)
    reporter = Column(String, nullable=True)
    page = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Enhancement model for suggested improvements
class Enhancement(Base):
    __tablename__ = "enhancements"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    description = Column(Text)
    suggested_by = Column(String, nullable=True)
    page = Column(String, nullable=True)
    tags = Column(String, default="")
    categories = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")
    proposal_id = Column(String, nullable=True, default=None)  # New: reference to original proposal
    project = Column(String, index=True, nullable=True)  # Project association

# Initialize the database and create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Usage: from db import SessionLocal, init_db 