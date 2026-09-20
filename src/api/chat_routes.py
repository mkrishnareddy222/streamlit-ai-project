from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from service.chat_service import (
    create_thread,
    get_thread_history,
    list_user_threads,
    remove_thread,
)

router = APIRouter(prefix="/api", tags=["chat"])


class CreateChatThreadRequest(BaseModel):
    user_id: str
    title: str
    is_guest: bool = False


class CreateChatThreadResponse(BaseModel):
    thread_id: str


class ChatThreadSummary(BaseModel):
    thread_id: str
    title: str
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    timestamp: str


class ChatThreadResponse(ChatThreadSummary):
    user_id: str
    is_guest: bool
    messages: list[ChatMessageResponse]


@router.post("/threads", response_model=CreateChatThreadResponse, status_code=201)
def create_chat_thread(request: CreateChatThreadRequest) -> CreateChatThreadResponse:
    thread_id = create_thread(
        user_id=request.user_id,
        title=request.title,
        is_guest=request.is_guest,
    )
    return CreateChatThreadResponse(thread_id=thread_id)


@router.get("/threads", response_model=list[ChatThreadSummary])
def get_recent_threads(user_id: str, limit: int = 20) -> list[ChatThreadSummary]:
    threads = list_user_threads(user_id=user_id, limit=min(limit, 50))
    return [
        ChatThreadSummary(
            thread_id=thread["_id"],
            title=thread["title"],
            created_at=thread["created_at"].isoformat(),
            updated_at=thread["updated_at"].isoformat(),
        )
        for thread in threads
    ]


@router.get("/threads/{thread_id}", response_model=ChatThreadResponse)
def get_thread(thread_id: str, user_id: str) -> ChatThreadResponse:
    thread = get_thread_history(user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found",
        )

    return ChatThreadResponse(
        thread_id=thread["_id"],
        user_id=thread["user_id"],
        title=thread["title"],
        is_guest=thread["is_guest"],
        created_at=thread["created_at"].isoformat(),
        updated_at=thread["updated_at"].isoformat(),
        messages=[
            ChatMessageResponse(
                message_id=message["message_id"],
                role=message["role"],
                content=message["content"],
                timestamp=message["timestamp"].isoformat(),
            )
            for message in thread.get("messages", [])
        ],
    )


@router.delete("/threads/{thread_id}")
def delete_thread(thread_id: str, user_id: str) -> dict[str, str]:
    deleted = remove_thread(user_id=user_id, thread_id=thread_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found",
        )
    return {"message": "Chat thread deleted successfully"}
