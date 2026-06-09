from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    task_type: Mapped[str] = mapped_column(
        Enum("research", "generate", name="generation_task_type"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "done", "failed", name="generation_task_status"),
        nullable=False,
        server_default="pending",
    )
    step: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "research",
            "topic_candidates",
            "knowledge",
            "questions",
            "done",
            "failed",
            name="generation_task_step",
        ),
        nullable=False,
        server_default="pending",
    )
    progress_message: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
