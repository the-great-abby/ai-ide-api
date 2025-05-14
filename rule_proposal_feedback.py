import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum, Text, DateTime
from db import Base

class FeedbackType(str, enum.Enum):
    accept = "accept"
    reject = "reject"
    needs_changes = "needs_changes"

class RuleProposalFeedback(Base):
    __tablename__ = "rule_proposal_feedback"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_proposal_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)  # No user model yet
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 