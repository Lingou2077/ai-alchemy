from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import settings
from db.models.generation_task import GenerationTask
from db.session import get_session_factory
from schemas.question import GenerateQuestionsRequest, GenerateQuestionsResponse
from schemas.research import ResearchResponse
from schemas.task import (
    GenerateTaskStatusResponse,
    ResearchSessionSnapshot,
    ResearchTaskStatusResponse,
    TaskCreatedResponse,
    TaskStatus,
    TaskStep,
    TaskType,
)
from services.content_utils import normalize_content
from services.question_pipeline import build_generate_response, run_question_pipeline
from services.research.research_service import get_research_session_or_410, run_research

logger = logging.getLogger(__name__)

StepCallback = Callable[[TaskStep, str], None]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _task_ttl() -> datetime:
    return _utcnow() + timedelta(seconds=settings.generation_task_ttl_seconds)


def _get_task_or_404(db: Session, task_id: str, task_type: TaskType) -> GenerationTask:
    task = (
        db.query(GenerationTask)
        .filter(GenerationTask.task_id == task_id, GenerationTask.task_type == task_type.value)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.expires_at < _utcnow():
        raise HTTPException(status_code=410, detail="任务已过期，请重新发起")
    return task


def _update_task(
    db: Session,
    task: GenerationTask,
    *,
    status: TaskStatus | None = None,
    step: TaskStep | None = None,
    progress_message: str | None = None,
    result: dict | None = None,
    error_message: str | None = None,
    session_id: str | None = None,
) -> None:
    if status is not None:
        task.status = status.value
    if step is not None:
        task.step = step.value
    if progress_message is not None:
        task.progress_message = progress_message
    if result is not None:
        task.result = result
    if error_message is not None:
        task.error_message = error_message
    if session_id is not None:
        task.session_id = session_id
    db.commit()


def _build_research_snapshot(research_session_id: str) -> dict[str, Any]:
    research_session = get_research_session_or_410(research_session_id)
    snapshot = ResearchSessionSnapshot(
        research_session_id=research_session_id,
        user_content=research_session.user_content,
        materials=[item.model_dump() for item in research_session.materials],
        candidates=[item.model_dump() for item in research_session.candidates],
        input_kind=research_session.input_kind.value,
        degraded_mode=research_session.degraded_mode.value,
        mock_mode=research_session.mock_mode,
    )
    return snapshot.model_dump()


def create_research_task(db: Session, content: str, user_id: int | None = None) -> TaskCreatedResponse:
    normalized_content, _ = normalize_content(content)
    task_id = str(uuid.uuid4())
    task = GenerationTask(
        task_id=task_id,
        task_type=TaskType.research.value,
        user_id=user_id,
        status=TaskStatus.pending.value,
        step=TaskStep.pending.value,
        progress_message="任务已创建",
        request_payload={"content": normalized_content},
        expires_at=_task_ttl(),
    )
    db.add(task)
    db.commit()
    schedule_research_task(task_id)
    return TaskCreatedResponse(task_id=task_id)


def create_generate_task(
    db: Session,
    request: GenerateQuestionsRequest,
    user_id: int | None = None,
) -> TaskCreatedResponse:
    normalized_content, _ = normalize_content(request.content)
    payload: dict[str, Any] = {
        "content": normalized_content,
        "questions_per_level": request.questions_per_level,
        "research_session_id": request.research_session_id,
        "selected_topic_id": request.selected_topic_id,
    }
    if request.research_session_id and request.selected_topic_id:
        payload["research_snapshot"] = _build_research_snapshot(request.research_session_id)

    task_id = str(uuid.uuid4())
    task = GenerationTask(
        task_id=task_id,
        task_type=TaskType.generate.value,
        user_id=user_id,
        status=TaskStatus.pending.value,
        step=TaskStep.pending.value,
        progress_message="任务已创建",
        request_payload=payload,
        expires_at=_task_ttl(),
    )
    db.add(task)
    db.commit()
    schedule_generate_task(task_id)
    return TaskCreatedResponse(task_id=task_id)


def get_research_task_status(db: Session, task_id: str) -> ResearchTaskStatusResponse:
    task = _get_task_or_404(db, task_id, TaskType.research)
    result = ResearchResponse.model_validate(task.result) if task.result else None
    return ResearchTaskStatusResponse(
        task_id=task.task_id,
        status=TaskStatus(task.status),
        step=TaskStep(task.step),
        progress_message=task.progress_message,
        error_message=task.error_message,
        result=result,
    )


def get_generate_task_status(db: Session, task_id: str) -> GenerateTaskStatusResponse:
    task = _get_task_or_404(db, task_id, TaskType.generate)
    result = GenerateQuestionsResponse.model_validate(task.result) if task.result else None
    return GenerateTaskStatusResponse(
        task_id=task.task_id,
        status=TaskStatus(task.status),
        step=TaskStep(task.step),
        progress_message=task.progress_message,
        error_message=task.error_message,
        result=result,
    )


def schedule_research_task(task_id: str) -> None:
    asyncio.create_task(_execute_research_task(task_id))


def schedule_generate_task(task_id: str) -> None:
    asyncio.create_task(_execute_generate_task(task_id))


async def _execute_research_task(task_id: str) -> None:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        task = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
        if task is None:
            return

        _update_task(
            db,
            task,
            status=TaskStatus.running,
            step=TaskStep.research,
            progress_message="联网检索中…",
        )

        def on_step(step: TaskStep, message: str) -> None:
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh is None:
                return
            _update_task(db, fresh, step=step, progress_message=message)

        content = str(task.request_payload.get("content", ""))
        try:
            on_step(TaskStep.research, "联网检索中…")
            response = await run_research(content)
            on_step(TaskStep.topic_candidates, "整理候选主题…")
            _update_task(
                db,
                db.query(GenerationTask).filter(GenerationTask.task_id == task_id).one(),
                status=TaskStatus.done,
                step=TaskStep.done,
                progress_message="检索完成",
                result=response.model_dump(mode="json"),
            )
        except HTTPException as exc:
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh:
                _update_task(
                    db,
                    fresh,
                    status=TaskStatus.failed,
                    step=TaskStep.failed,
                    progress_message="检索失败",
                    error_message=str(exc.detail),
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("research task %s failed", task_id)
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh:
                _update_task(
                    db,
                    fresh,
                    status=TaskStatus.failed,
                    step=TaskStep.failed,
                    progress_message="检索失败",
                    error_message="联网检索失败，请稍后重试",
                )
    finally:
        db.close()


async def _execute_generate_task(task_id: str) -> None:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        task = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
        if task is None:
            return

        _update_task(
            db,
            task,
            status=TaskStatus.running,
            step=TaskStep.knowledge,
            progress_message="正在解析知识…",
        )

        def on_step(step: TaskStep, message: str) -> None:
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh is None:
                return
            _update_task(db, fresh, step=step, progress_message=message)

        payload = task.request_payload
        research_snapshot = payload.get("research_snapshot")
        try:
            session_id, knowledge, questions, truncated, grounded = await run_question_pipeline(
                str(payload["content"]),
                int(payload.get("questions_per_level", 5)),
                research_session_id=payload.get("research_session_id"),
                selected_topic_id=payload.get("selected_topic_id"),
                research_snapshot=research_snapshot,
                on_step=on_step,
            )
            response = build_generate_response(session_id, knowledge, questions, truncated, grounded)
            _update_task(
                db,
                db.query(GenerationTask).filter(GenerationTask.task_id == task_id).one(),
                status=TaskStatus.done,
                step=TaskStep.done,
                progress_message="题目已生成",
                result=response.model_dump(mode="json"),
                session_id=session_id,
            )
        except HTTPException as exc:
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh:
                _update_task(
                    db,
                    fresh,
                    status=TaskStatus.failed,
                    step=TaskStep.failed,
                    progress_message="生成失败",
                    error_message=str(exc.detail),
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("generate task %s failed", task_id)
            fresh = db.query(GenerationTask).filter(GenerationTask.task_id == task_id).first()
            if fresh:
                _update_task(
                    db,
                    fresh,
                    status=TaskStatus.failed,
                    step=TaskStep.failed,
                    progress_message="生成失败",
                    error_message="知识解析失败，请精简内容后重试",
                )
    finally:
        db.close()
