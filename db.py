from sqlalchemy import create_engine, Column, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import BLOB
from datetime import datetime
import enum
import uuid

# SQLite database URL
DATABASE_URL = "sqlite:///rules.db"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum for rule/proposal/feedback status
class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

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

# Proposal model
class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_type = Column(String, index=True)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    submitted_by = Column(String, index=True)
    project = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

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

# Initialize the database and create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Usage: from db import SessionLocal, init_db 