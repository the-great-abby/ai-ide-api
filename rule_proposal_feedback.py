import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from db import Base


class RuleProposalFeedback(Base):
    __tablename__ = "rule_proposal_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    rule_proposal_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # No user model yet
    feedback_type = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
