"""Stage-1 non-streaming chat/RAG route."""

from __future__ import annotations

import asyncio
import json
from functools import partial

import anyio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ...config import AppConfig
from ...services.chat_service import (
    ChatLearningGoalError,
    ChatModelUnavailableError,
    prefetch_api_chat_token,
)
from ...services.identity_service import StudentContext
from ..dependencies import ApiServices, get_api_services, get_config, get_student_context
from ..errors import ApiDomainError
from ..schemas.adapters import api_chat_done_payload, api_chat_to_response
from ..schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _raise_chat_error(exc: Exception, config: AppConfig) -> None:
    """Map pre-response chat failures to the stable error envelope."""
    if isinstance(exc, TimeoutError):
        raise ApiDomainError(
            "chat_timeout",
            "The chat request exceeded its local processing timeout.",
            f"Timeout after {config.api_chat_timeout_seconds} seconds.",
            True,
            504,
        ) from exc
    if isinstance(exc, ChatLearningGoalError):
        raise ApiDomainError(
            "invalid_learning_goal",
            "The learning goal is not valid for this subject scope.",
            str(exc),
            False,
            422,
        ) from exc
    if isinstance(exc, ChatModelUnavailableError):
        raise ApiDomainError(
            "model_unavailable", "The selected model is unavailable.", str(exc), True, 503
        ) from exc
    raise exc


async def _bounded_thread(operation, config: AppConfig):
    return await asyncio.wait_for(
        anyio.to_thread.run_sync(operation, abandon_on_cancel=True),
        timeout=config.api_chat_timeout_seconds,
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"


@router.post(
    "",
    response_model=ChatResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def chat(
    payload: ChatRequest,
    request: Request,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> ChatResponse:
    """Generate one grounded answer without persisting an authoritative transcript."""
    common = dict(
        subject_id=payload.subject_id,
        component_subject_id=payload.component_subject_id,
        language=payload.language,
        question=payload.question,
        learning_goal_id=payload.learning_goal_id,
        material_ids=payload.material_ids,
        top_k=payload.top_k,
        student=student,
        config=config,
    )
    if payload.stream:
        try:
            prepared = await _bounded_thread(partial(services.prepare_chat, **common), config)
            iterator = services.open_chat_stream(prepared, config=config)
            has_token, first_token = await _bounded_thread(
                partial(prefetch_api_chat_token, iterator), config
            )
            if not has_token:
                raise ChatModelUnavailableError("The streaming model returned no tokens")
        except Exception as exc:
            _raise_chat_error(exc, config)

        async def event_stream():
            answer_parts: list[str] = []
            try:
                token = first_token
                while True:
                    if await request.is_disconnected():
                        return
                    answer_parts.append(token)
                    yield _sse("token", {"delta": token})
                    try:
                        has_next, token = await _bounded_thread(
                            partial(prefetch_api_chat_token, iterator), config
                        )
                    except Exception as exc:
                        yield _sse(
                            "error",
                            {
                                "code": "stream_failed",
                                "message": "The model stream failed after generation began.",
                                "detail": exc.__class__.__name__,
                                "retryable": True,
                                "request_id": str(request.state.request_id),
                            },
                        )
                        return
                    if not has_next:
                        break
                try:
                    result = await _bounded_thread(
                        partial(
                            services.finalize_chat,
                            prepared,
                            "".join(answer_parts),
                            student=student,
                            config=config,
                            thread_id=payload.thread_id,
                        ),
                        config,
                    )
                except Exception as exc:
                    yield _sse(
                        "error",
                        {
                            "code": "stream_finalize_failed",
                            "message": "The answer completed but its metadata could not be finalized.",
                            "detail": exc.__class__.__name__,
                            "retryable": True,
                            "request_id": str(request.state.request_id),
                        },
                    )
                    return
                yield _sse(
                    "done",
                    api_chat_done_payload(result, include_sources=payload.include_sources),
                )
            except asyncio.CancelledError:
                raise
            finally:
                close = getattr(iterator, "close", None)
                if close is not None:
                    close()

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    operation = partial(services.chat, **common, thread_id=payload.thread_id)
    try:
        result = await _bounded_thread(operation, config)
    except Exception as exc:
        _raise_chat_error(exc, config)
    return api_chat_to_response(
        result,
        thread_id=payload.thread_id,
        language=payload.language,
        include_sources=payload.include_sources,
    )
