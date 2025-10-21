# FIX: Rename uuid import to avoid namespace conflict
import uuid as uuid_lib
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from sqlalchemy import (
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    Float,
    UUID as SA_UUID,
    func, 
    Date,
    Index
)
from sqlalchemy.dialects.postgresql import JSON as PG_JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from src.db.database import Base

# ------------------------- Core User and Session Models -------------------------

class User(Base):
    __tablename__ = "users"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    hashed_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    google_provider_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    pfpb: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # profile picture
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # --- Relationships ---
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notification_preferences: Mapped[Optional["NotificationPreference"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memory_entities: Mapped[List["MemoryEntity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_calls: Mapped[List["ApiCall"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    summaries: Mapped[List["ConversationSummary"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"
    # ... (no changes to this model)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    user: Mapped["User"] = relationship(back_populates="sessions")


# ------------------------- Job and Task Processing Models -------------------------

class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", index=True, nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    extra_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)

    # Updated timestamps with added updated_at field
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), 
                                                onupdate=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="tasks")
    task_results: Mapped[List["TaskResult"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskResult(Base):
    __tablename__ = "task_results"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    task_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("tasks.uuid"), nullable=False)

    result: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Updated to server-side timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="task_results")


# ------------------------- Notification Models -------------------------

class Notification(Base):
    __tablename__ = "notifications"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Updated to server-side timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), unique=True, nullable=False)

    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Updated to server-side timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), 
                                                onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notification_preferences")


# ------------------------- Conversation and Memory Models -------------------------

# ------------------------- Conversation and Memory Models -------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="conversations")
    memory_entities: Mapped[List["MemoryEntity"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    summary: Mapped[Optional["ConversationSummary"]] = relationship(back_populates="conversation", uselist=False, cascade="all, delete-orphan")
class MemoryEntity(Base):
    __tablename__ = "memory_entities"
    # ... (no changes to this model)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)
    conversation_id: Mapped[Optional[uuid_lib.UUID]] = mapped_column(ForeignKey("conversations.uuid"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    extra_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    importance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user: Mapped["User"] = relationship(back_populates="memory_entities")
    conversation: Mapped[Optional["Conversation"]] = relationship(back_populates="memory_entities")



# ------------------------- Vector and Processing Job Models -------------------------

class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    entity_id: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)

    vector: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)

    # Updated to server-side timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), 
                                                onupdate=func.now(), nullable=False)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False, index=True)
    user: Mapped["User"] = relationship(back_populates="processing_jobs")
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", index=True, nullable=False)

    input_data: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    result_data: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Updated to server-side timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


# ------------------------- System and API Models -------------------------

class ApiCall(Base):
    __tablename__ = "api_calls"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    user_id: Mapped[Optional[uuid_lib.UUID]] = mapped_column(ForeignKey("users.uuid"), nullable=True)

    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    request_data: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    response_data: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    token_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Updated to server-side timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="api_calls")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Updated to server-side timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), 
                                                onupdate=func.now(), nullable=False)
    updated_by: Mapped[Optional[uuid_lib.UUID]] = mapped_column(ForeignKey("users.uuid"), nullable=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    conversation_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("conversations.uuid"), nullable=False, index=True)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False, index=True)
    job_id: Mapped[Optional[uuid_lib.UUID]] = mapped_column(SA_UUID(as_uuid=True), nullable=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(PG_JSON, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user: Mapped["User"] = relationship(back_populates="chat_messages")
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    __table_args__ = (Index("ix_chat_messages_conversation_created_at", "conversation_id", "created_at"),)

class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    uuid: Mapped[uuid_lib.UUID] = mapped_column(SA_UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    conversation_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("conversations.uuid"), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid_lib.UUID] = mapped_column(ForeignKey("users.uuid"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="summaries")
    conversation: Mapped["Conversation"] = relationship(back_populates="summary", uselist=False)
