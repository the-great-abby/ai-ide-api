import uuid
from datetime import datetime

class Rule:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.rule_type = kwargs.get('rule_type', '')
        self.description = kwargs.get('description', '')
        self.diff = kwargs.get('diff', '')
        self.status = kwargs.get('status', 'approved')
        self.submitted_by = kwargs.get('submitted_by', '')
        self.added_by = kwargs.get('added_by', None)
        self.project = kwargs.get('project', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.version = kwargs.get('version', 1)
        self.categories = kwargs.get('categories', '')
        self.tags = kwargs.get('tags', '')
        self.examples = kwargs.get('examples', None)
        self.applies_to = kwargs.get('applies_to', '')
        self.applies_to_rationale = kwargs.get('applies_to_rationale', None)
        self.user_story = kwargs.get('user_story', None)
        self.scope_level = kwargs.get('scope_level', 'global')
        self.scope_id = kwargs.get('scope_id', None)
        self.parent_rule_id = kwargs.get('parent_rule_id', None)

class Proposal:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.rule_id = kwargs.get('rule_id', None)
        self.rule_type = kwargs.get('rule_type', '')
        self.description = kwargs.get('description', '')
        self.diff = kwargs.get('diff', '')
        self.status = kwargs.get('status', 'pending')
        self.submitted_by = kwargs.get('submitted_by', '')
        self.project = kwargs.get('project', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.version = kwargs.get('version', 1)
        self.categories = kwargs.get('categories', '')
        self.tags = kwargs.get('tags', '')
        self.examples = kwargs.get('examples', None)
        self.applies_to = kwargs.get('applies_to', '')
        self.applies_to_rationale = kwargs.get('applies_to_rationale', None)
        self.reason_for_change = kwargs.get('reason_for_change', None)
        self.references = kwargs.get('references', None)
        self.current_rule = kwargs.get('current_rule', None)
        self.user_story = kwargs.get('user_story', None)
        self.scope_level = kwargs.get('scope_level', 'global')
        self.scope_id = kwargs.get('scope_id', None)
        self.parent_rule_id = kwargs.get('parent_rule_id', None)

class Feedback:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.rule_id = kwargs.get('rule_id', '')
        self.project = kwargs.get('project', None)
        self.feedback_type = kwargs.get('feedback_type', '')
        self.comment = kwargs.get('comment', None)
        self.submitted_by = kwargs.get('submitted_by', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())

class RuleVersion:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.rule_id = kwargs.get('rule_id', '')
        self.version = kwargs.get('version', 1)
        self.rule_type = kwargs.get('rule_type', '')
        self.description = kwargs.get('description', '')
        self.diff = kwargs.get('diff', '')
        self.status = kwargs.get('status', 'approved')
        self.submitted_by = kwargs.get('submitted_by', '')
        self.added_by = kwargs.get('added_by', None)
        self.project = kwargs.get('project', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.categories = kwargs.get('categories', '')
        self.tags = kwargs.get('tags', '')
        self.examples = kwargs.get('examples', None)
        self.applies_to = kwargs.get('applies_to', '')
        self.applies_to_rationale = kwargs.get('applies_to_rationale', None)
        self.user_story = kwargs.get('user_story', None)
        self.scope_level = kwargs.get('scope_level', 'global')
        self.scope_id = kwargs.get('scope_id', None)
        self.parent_rule_id = kwargs.get('parent_rule_id', None)

class BugReport:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.description = kwargs.get('description', '')
        self.reporter = kwargs.get('reporter', None)
        self.page = kwargs.get('page', None)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.user_story = kwargs.get('user_story', None)

class Enhancement:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.description = kwargs.get('description', '')
        self.suggested_by = kwargs.get('suggested_by', None)
        self.page = kwargs.get('page', None)
        self.tags = kwargs.get('tags', '')
        self.categories = kwargs.get('categories', '')
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.status = kwargs.get('status', 'open')
        self.proposal_id = kwargs.get('proposal_id', None)
        self.project = kwargs.get('project', None)
        self.examples = kwargs.get('examples', None)
        self.applies_to = kwargs.get('applies_to', '')
        self.applies_to_rationale = kwargs.get('applies_to_rationale', None)
        self.user_story = kwargs.get('user_story', None)
        self.diff = kwargs.get('diff', None)
        self.scope_level = kwargs.get('scope_level', 'global')
        self.scope_id = kwargs.get('scope_id', None)
        self.parent_rule_id = kwargs.get('parent_rule_id', None)

class ApiErrorLog:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.path = kwargs.get('path', '')
        self.method = kwargs.get('method', '')
        self.status_code = kwargs.get('status_code', 200)
        self.message = kwargs.get('message', '')
        self.stack_trace = kwargs.get('stack_trace', '')
        self.user_id = kwargs.get('user_id', None)

class ApiAccessToken:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.token = kwargs.get('token', '')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.created_by = kwargs.get('created_by', None)
        self.description = kwargs.get('description', None)
        self.active = kwargs.get('active', 1)
        self.role = kwargs.get('role', 'admin')

class MemoryVector:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.namespace = kwargs.get('namespace', '')
        self.reference_id = kwargs.get('reference_id', '')
        self.content = kwargs.get('content', '')
        self.embedding = kwargs.get('embedding', None)
        self.meta = kwargs.get('meta', None)
        self.created_at = kwargs.get('created_at', datetime.utcnow())

class MemoryEdge:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.from_id = kwargs.get('from_id', '')
        self.to_id = kwargs.get('to_id', '')
        self.relation_type = kwargs.get('relation_type', '')
        self.meta = kwargs.get('meta', None)
        self.created_at = kwargs.get('created_at', datetime.utcnow())

class Project:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', None)
        self.created_at = kwargs.get('created_at', datetime.utcnow())

class ProjectMembership:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id', '')
        self.project_id = kwargs.get('project_id', '')
        self.role = kwargs.get('role', 'admin')

class ProjectOnboardingProgress:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.project_id = kwargs.get('project_id', '')
        self.step = kwargs.get('step', '')
        self.completed = kwargs.get('completed', False)
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.details = kwargs.get('details', None)

class UseCase:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.example_workflow = kwargs.get('example_workflow', None)
        self.tags = kwargs.get('tags', '')
        self.categories = kwargs.get('categories', '')
        self.submitted_by = kwargs.get('submitted_by', None)
        self.status = kwargs.get('status', 'pending')
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.source = kwargs.get('source', None) 