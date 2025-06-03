import enum
import os
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.types import UserDefinedType

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


# Add support for pgvector
class Vector(UserDefinedType):
    def get_col_spec(self, **kw):
        return "vector(768)"  # Adjust dimension as needed


# MemoryDB connection (for vector store)
MEMORYDB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/memorydb"
memory_engine = create_engine(MEMORYDB_URL)
MemorySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=memory_engine)


# Enum for rule/proposal/feedback status
class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    reverted_to_enhancement = "reverted_to_enhancement"  # New status


# Enum for scope level
class ScopeLevelEnum(str, enum.Enum):
    global_ = "global"
    team = "team"
    project = "project"
    machine = "machine"


# Allowed values for scope_level: 'global', 'team', 'project', 'machine'


# Rule model
class Rule(Base):
    __tablename__ = "rules"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    rule_type = Column(String, index=True)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.approved)
    submitted_by = Column(String, index=True)
    added_by = Column(String, index=True, nullable=True)
    project = Column(UUID(as_uuid=True), index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    categories = Column(String, default="")  # Comma-separated
    tags = Column(String, default="")  # Comma-separated
    examples = Column(Text, nullable=True, default=None)
    applies_to = Column(String, default="")  # Comma-separated list of targets
    applies_to_rationale = Column(Text, nullable=True, default=None)
    user_story = Column(Text, nullable=True, default=None)
    # Hierarchical scope fields
    scope_level = Column(
        String, index=True, nullable=False, default="global"
    )  # 'global', 'team', 'project', 'machine'
    scope_id = Column(String, index=True, nullable=True)
    parent_rule_id = Column(String, nullable=True)


# Proposal model
class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    rule_id = Column(
        UUID(as_uuid=True), ForeignKey("rules.id"), nullable=True
    )  # Reference to rule being updated
    rule_type = Column(String, index=True)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    submitted_by = Column(String, index=True)
    project = Column(UUID(as_uuid=True), index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    categories = Column(String, default="")  # Comma-separated
    tags = Column(String, default="")  # Comma-separated
    examples = Column(Text, nullable=True, default=None)
    applies_to = Column(String, default="")  # Comma-separated list of targets
    applies_to_rationale = Column(Text, nullable=True, default=None)
    reason_for_change = Column(Text, nullable=True, default=None)
    references = Column(Text, nullable=True, default=None)
    current_rule = Column(Text, nullable=True, default=None)
    user_story = Column(Text, nullable=True, default=None)
    # Hierarchical scope fields
    scope_level = Column(
        String, index=True, nullable=False, default="global"
    )  # 'global', 'team', 'project', 'machine'
    scope_id = Column(String, index=True, nullable=True)
    parent_rule_id = Column(
        UUID(as_uuid=True), ForeignKey("rules.id"), nullable=True
    )  # Reference to parent rule for versioning


# Feedback model
class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    rule_id = Column(UUID(as_uuid=True), index=True)
    project = Column(UUID(as_uuid=True), index=True, nullable=True)
    feedback_type = Column(String)
    comment = Column(Text, nullable=True)
    submitted_by = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# RuleVersion model for version history
class RuleVersion(Base):
    __tablename__ = "rule_versions"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    rule_id = Column(UUID(as_uuid=True), index=True)
    version = Column(Integer)
    rule_type = Column(String)
    description = Column(Text)
    diff = Column(Text)
    status = Column(Enum(StatusEnum))
    submitted_by = Column(String)
    added_by = Column(String, nullable=True)
    project = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime)
    categories = Column(String, default="")
    tags = Column(String, default="")
    examples = Column(Text, nullable=True, default=None)
    applies_to = Column(String, default="")  # Comma-separated list of targets
    applies_to_rationale = Column(Text, nullable=True, default=None)
    user_story = Column(Text, nullable=True, default=None)
    # Hierarchical scope fields
    scope_level = Column(
        String, index=True, nullable=False, default="global"
    )  # 'global', 'team', 'project', 'machine'
    scope_id = Column(String, index=True, nullable=True)
    parent_rule_id = Column(String, nullable=True)


# BugReport model for bug reporting
class BugReport(Base):
    __tablename__ = "bug_reports"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    description = Column(Text)
    reporter = Column(String, nullable=True)
    page = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_story = Column(String, nullable=True)


# Enhancement model for suggested improvements
class Enhancement(Base):
    __tablename__ = "enhancements"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    description = Column(Text)
    suggested_by = Column(String, nullable=True)
    page = Column(String, nullable=True)
    tags = Column(String, default="")
    categories = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="open")
    proposal_id = Column(
        UUID(as_uuid=True), nullable=True, default=None
    )  # New: reference to original proposal
    project = Column(
        UUID(as_uuid=True), index=True, nullable=True
    )  # Project association
    examples = Column(Text, nullable=True, default=None)  # New field for examples
    applies_to = Column(String, default="")  # Comma-separated list of targets
    applies_to_rationale = Column(Text, nullable=True, default=None)
    user_story = Column(Text, nullable=True, default=None)
    diff = Column(Text, nullable=True, default=None)  # New: diff for enhancements
    # Hierarchical scope fields
    scope_level = Column(
        String, index=True, nullable=False, default="global"
    )  # 'global', 'team', 'project', 'machine'
    scope_id = Column(String, index=True, nullable=True)
    parent_rule_id = Column(String, nullable=True)


# --- New: API Error Log model ---
class ApiErrorLog(Base):
    __tablename__ = "api_error_logs"
    id = Column(UUID(as_uuid=True), primary_key=True)  # error_id (UUID)
    timestamp = Column(DateTime, default=datetime.utcnow)
    path = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    message = Column(Text)
    stack_trace = Column(Text)
    user_id = Column(String, nullable=True)  # If available


# --- New: Namespace Permission Models ---
class NamespacePermission(Base):
    __tablename__ = "namespace_permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    namespace = Column(String, nullable=False, index=True)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )  # Link to Project
    allowed_project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )  # Link to allowed Project
    permission_type = Column(String, nullable=False)  # "read" or "write"
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    active = Column(Integer, default=1)  # 1 = active, 0 = revoked


# Pydantic model for creating namespace permissions
class NamespacePermissionCreate:
    namespace: str
    project_id: str
    allowed_project_id: Optional[str] = None
    permission_type: str  # "read" or "write"


# Update ApiAccessToken to support scoping
class ApiAccessToken(Base):
    __tablename__ = "api_access_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    description = Column(String, nullable=True)
    active = Column(Integer, default=1)  # 1 = active, 0 = revoked
    role = Column(String(32), default="admin", nullable=False)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )  # Link to Project
    allowed_namespaces = Column(
        JSON, nullable=True
    )  # List of namespaces this token can access
    namespace_permissions = Column(
        String, nullable=True
    )  # JSON string of namespace:permission_type mappings
    has_llm_access = Column(Integer, default=0)  # 1 = has LLM access, 0 = no LLM access


# Vector store model
class MemoryVector(Base):
    __tablename__ = "memory_vectors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    namespace = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector, nullable=True)
    meta = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )  # Link to Project


# Edge/relationship model for memory graph
class MemoryEdge(Base):
    __tablename__ = "memory_edges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_id = Column(String, index=True)
    to_id = Column(String, index=True)
    relation_type = Column(String, index=True)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- New: Project model ---
class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    active = Column(Integer, default=1)  # 1 = active, 0 = archived
    has_llm_access = Column(Integer, default=0)  # 1 = has LLM access, 0 = no LLM access
    default_namespace = Column(String, nullable=False)  # e.g., "project-name/private"
    namespace_prefix = Column(String, nullable=False)  # e.g., "project-name"


# --- New: ProjectMembership model ---
class ProjectMembership(Base):
    __tablename__ = "project_memberships"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String, default="admin")  # For now, everyone is admin
    # Optionally, add unique constraint on (user_id, project_id) in migration


# --- New: ProjectOnboardingProgress model ---
class ProjectOnboardingProgress(Base):
    __tablename__ = "project_onboarding_progress"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(UUID(as_uuid=True), nullable=False)
    path = Column(String, nullable=False)  # New: onboarding process type
    step = Column(String, nullable=False)
    completed = Column(sa.Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(sa.JSON, nullable=True)
    version = Column(
        sa.Integer, nullable=False, default=1
    )  # New: version field for multiple attempts

    __table_args__ = (
        sa.UniqueConstraint(
            "project_id",
            "path",
            "step",
            "version",
            name="uix_project_path_step_version",
        ),
    )


# UseCase model for collaborative use-case submissions
class UseCase(Base):
    __tablename__ = "use_cases"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    example_workflow = Column(sa.JSON, nullable=False)
    tags = Column(String(255), default="")
    categories = Column(String(255), default="")
    submitted_by = Column(String(255), nullable=True)
    status = Column(String(32), default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(255), nullable=True)


# RuleProposal model
class RuleProposal(Base):
    __tablename__ = "rule_proposals"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="pending")
    submitted_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    feedback = Column(Text, nullable=True)


# --- New: Team model ---
class Team(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    active = Column(Integer, default=1)


# Initialize the database and create tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Initialize the memorydb and create tables
def init_memorydb():
    Base.metadata.create_all(bind=memory_engine)


# Example usage:
# from db import MemorySessionLocal, MemoryVector, init_memorydb
# session = MemorySessionLocal()
# vector = MemoryVector(namespace="test", reference_id="abc123", embedding=[0.1]*768, metadata="{}")
# session.add(vector)
# session.commit()
# session.close()

# Example vector search (cosine distance):
# session.execute(text("SELECT *, embedding <=> :query_vec AS distance FROM memory_vectors ORDER BY distance LIMIT 5"), {"query_vec": [0.1]*768})

# Example usage for edges:
# from db import MemorySessionLocal, MemoryEdge
# session = MemorySessionLocal()
# edge = MemoryEdge(from_id="uuid1", to_id="uuid2", relation_type="inspired_by", metadata="{}")
# session.add(edge)
# session.commit()
# session.close()

# Usage: from db import SessionLocal, init_db


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_project_by_name(db: Session, name: str, **kwargs):
    """
    Get or create a Project by name. If creating, requires default_namespace and namespace_prefix in kwargs.
    Handles race conditions by retrying fetch on IntegrityError.
    """
    project = db.query(Project).filter(Project.name == name).first()
    if project:
        return project
    # Ensure required fields are present
    if "default_namespace" not in kwargs or "namespace_prefix" not in kwargs:
        raise ValueError(
            "default_namespace and namespace_prefix are required to create a new Project"
        )
    project = Project(name=name, **kwargs)
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(Project).filter(Project.name == name).first()
    db.expire_all()
    db.refresh(project)
    return project


def get_or_create_team_by_name(db: Session, name: str, **kwargs):
    """
    Get or create a Team by name. Handles race conditions by retrying fetch on IntegrityError.
    """
    team = db.query(Team).filter(Team.name == name).first()
    if team:
        return team
    team = Team(name=name, **kwargs)
    db.add(team)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(Team).filter(Team.name == name).first()
    db.expire_all()
    db.refresh(team)
    return team
