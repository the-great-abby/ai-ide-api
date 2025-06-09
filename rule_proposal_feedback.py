import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from db import Base, resolve_project_id, resolve_team_id

# ARR! All IDs and foreign keys be sa.String() for maximum compatibility. No UUID columns! See ONBOARDING_INTERNAL.md and rules/db_types.mdc for the tale.

class RuleProposalFeedback(Base):
    __tablename__ = "rule_proposal_feedback"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_proposal_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)  # No user model yet
    feedback_type = Column(String, nullable=False)  # Always a string!
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
