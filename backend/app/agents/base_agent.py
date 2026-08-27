from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import utcnow
from app.models.agent_run import AgentRun, AgentRunStatus
from app.services.openai_service import get_openai_service

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, name: str, prompt_version: str = "1.0") -> None:
        self.name = name
        self.prompt_version = prompt_version
        self.openai_service = get_openai_service()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_user_prompt(self, input_data: dict[str, Any]) -> str:
        """Return the user prompt based on input data."""
        pass

    @abstractmethod
    def get_response_schema(self) -> type[T]:
        """Return the Pydantic schema for structured output."""
        pass

    def execute(
        self,
        db: Session,
        course_id: uuid.UUID,
        input_data: dict[str, Any],
        max_tokens: int | None = None,
    ) -> T:
        """Execute the agent with logging and error handling."""
        agent_run = self._create_agent_run(db, course_id, input_data)
        
        try:
            logger.info(
                "agent_execution_started",
                agent_name=self.name,
                course_id=str(course_id),
                run_id=str(agent_run.id),
            )
            
            # Build messages
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": self.get_user_prompt(input_data)},
            ]
            
            # Execute structured completion
            response_schema = self.get_response_schema()
            result = self.openai_service.structured_completion(
                messages=messages,
                response_schema=response_schema,
                max_tokens=max_tokens,
            )
            
            # Update agent run with success
            self._update_agent_run_success(db, agent_run, result)
            
            logger.info(
                "agent_execution_completed",
                agent_name=self.name,
                course_id=str(course_id),
                run_id=str(agent_run.id),
                execution_time_ms=agent_run.execution_time_ms,
            )
            
            return result
            
        except Exception as exc:
            # Update agent run with failure
            self._update_agent_run_failure(db, agent_run, exc)
            
            logger.error(
                "agent_execution_failed",
                agent_name=self.name,
                course_id=str(course_id),
                run_id=str(agent_run.id),
                error=str(exc),
            )
            
            raise

    def _create_agent_run(
        self,
        db: Session,
        course_id: uuid.UUID,
        input_data: dict[str, Any],
    ) -> AgentRun:
        """Create and return a new agent run record."""
        agent_run = AgentRun(
            course_id=course_id,
            agent_name=self.name,
            prompt_version=self.prompt_version,
            input_data=input_data,
            status=AgentRunStatus.RUNNING,
            started_at=utcnow(),
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        return agent_run

    def _update_agent_run_success(
        self,
        db: Session,
        agent_run: AgentRun,
        result: BaseModel,
    ) -> None:
        """Update agent run with successful execution."""
        agent_run.status = AgentRunStatus.SUCCESS
        agent_run.output_data = result.model_dump()
        agent_run.completed_at = utcnow()
        _end = agent_run.completed_at
        _start = agent_run.started_at
        if _end is not None and _start is not None:
            if _end.tzinfo is not None and _start.tzinfo is None:
                _end = _end.replace(tzinfo=None)
            elif _start.tzinfo is not None and _end.tzinfo is None:
                _start = _start.replace(tzinfo=None)
            agent_run.execution_time_ms = int((_end - _start).total_seconds() * 1000)
        db.commit()
        db.refresh(agent_run)

    def _update_agent_run_failure(
        self,
        db: Session,
        agent_run: AgentRun,
        error: Exception,
    ) -> None:
        """Update agent run with failed execution."""
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(error)
        agent_run.completed_at = utcnow()
        _end = agent_run.completed_at
        _start = agent_run.started_at
        if _end is not None and _start is not None:
            if _end.tzinfo is not None and _start.tzinfo is None:
                _end = _end.replace(tzinfo=None)
            elif _start.tzinfo is not None and _end.tzinfo is None:
                _start = _start.replace(tzinfo=None)
            agent_run.execution_time_ms = int((_end - _start).total_seconds() * 1000)
        db.commit()
        db.refresh(agent_run)

    def get_execution_history(
        self,
        db: Session,
        course_id: uuid.UUID,
        limit: int = 10,
    ) -> list[AgentRun]:
        """Get execution history for this agent and course."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(AgentRun)
            .where(AgentRun.course_id == course_id)
            .where(AgentRun.agent_name == self.name)
            .order_by(AgentRun.started_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())
