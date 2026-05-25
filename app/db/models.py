import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


# ---- agent_configs ----
class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    prompt_versions = relationship("PromptVersion", back_populates="agent_config")
    conversations = relationship("Conversation", back_populates="agent_config")


# ---- conversations ----
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_config_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_configs.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    agent_config = relationship("AgentConfig", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    agent_runs = relationship("AgentRun", back_populates="conversation")


# ---- messages ----
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    conversation = relationship("Conversation", back_populates="messages")


# ---- agent_runs ----
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=True, index=True)
    graph_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="agent_runs")
    tool_calls = relationship("ToolCall", back_populates="agent_run")


# ---- tool_calls ----
class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    agent_run_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    output_result: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agent_run = relationship("AgentRun", back_populates="tool_calls")


# ---- prompt_versions ----
class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    agent_config_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_configs.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent_config = relationship("AgentConfig", back_populates="prompt_versions")


# ---- knowledge_docs ----
class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    chunks = relationship("KnowledgeChunk", back_populates="doc")


# ---- knowledge_chunks ----
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    doc_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_docs.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    doc = relationship("KnowledgeDoc", back_populates="chunks")


# ---- confirmation_records ----
class ConfirmationRecord(Base):
    __tablename__ = "confirmation_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_detail: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    risk_level: Mapped[str] = mapped_column(String(32), default="low")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ---- agent_safety_checks ----
class AgentSafetyCheck(Base):
    __tablename__ = "agent_safety_checks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=True, index=True)
    check_type: Mapped[str] = mapped_column(String(64), nullable=False)
    input_content: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ---- task_drafts ----
class TaskDraft(Base):
    __tablename__ = "task_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_post_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    safety_check_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_safety_checks.id"), nullable=True)
    confirmation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("confirmation_records.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ---- external_api_calls ----
class ExternalAPICall(Base):
    __tablename__ = "external_api_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=True, index=True)
    service_name: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    request_params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ---- reminder_drafts ----
class ReminderDraft(Base):
    __tablename__ = "reminder_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    remind_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    repeat_rule: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_fields: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    confirmation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("confirmation_records.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ---- reminders ----
class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    draft_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("reminder_drafts.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    repeat_rule: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ---- professional_agent_sessions ----
class ProfessionalAgentSession(Base):
    __tablename__ = "professional_agent_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("conversations.id"), nullable=True)
    handoff_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ---- handoff_records ----
class HandoffRecord(Base):
    __tablename__ = "handoff_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    external_user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("agent_runs.id"), nullable=True)
    from_agent: Mapped[str] = mapped_column(String(128), nullable=False)
    to_agent: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_session_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("professional_agent_sessions.id"), nullable=True)
    handoff_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmation_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("confirmation_records.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
