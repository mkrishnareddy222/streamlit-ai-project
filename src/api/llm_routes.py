import json
from typing import List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

from config import GROQ_API_KEY, MODEL_NAME
from service.chat_service import add_thread_message, create_thread

router = APIRouter(prefix="/api", tags=["llm"])
client = Groq(api_key=GROQ_API_KEY)


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMChatRequest(BaseModel):
    user_id: str
    messages: List[LLMMessage]
    thread_id: str | None = None
    title: str = "New chat"
    is_guest: bool = True


def stream_llm_response(request: LLMChatRequest):
    try:
        thread_id = request.thread_id
        if thread_id is None:
            thread_id = create_thread(
                user_id=request.user_id,
                title=request.title,
                is_guest=request.is_guest,
            )
            yield f"data: {json.dumps({'thread_id': thread_id})}\n\n"

        latest_message = request.messages[-1] if request.messages else None
        if latest_message and latest_message.role == "user":
            add_thread_message(
                thread_id=thread_id,
                role=latest_message.role,
                content=latest_message.content,
            )

        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[message.model_dump() for message in request.messages],
            temperature=0.2,
            max_tokens=500,
            stream=True,
        )
        assistant_content = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                assistant_content += content
                yield f"data: {json.dumps({'content': content})}\n\n"
        if assistant_content:
            add_thread_message(
                thread_id=thread_id,
                role="assistant",
                content=assistant_content,
            )
    except Exception as error:
        yield f"data: {json.dumps({'error': str(error)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("/chat/stream")
def chat_with_llm(request: LLMChatRequest):
    return StreamingResponse(
        stream_llm_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
