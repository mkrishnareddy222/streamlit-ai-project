from repo.database import (
    add_message_to_thread,
    create_chat_thread,
    delete_user_thread,
    get_user_chat_history,
    get_user_threads,
)


def create_thread(user_id: str, title: str, is_guest: bool = False) -> str:
    """Create a chat thread through the repository layer."""
    return create_chat_thread(user_id=user_id, title=title, is_guest=is_guest)


def add_thread_message(thread_id: str, role: str, content: str) -> None:
    """Append a user or assistant message through the repository layer."""
    add_message_to_thread(thread_id=thread_id, role=role, content=content)


def list_user_threads(user_id: str, limit: int = 20) -> list[dict]:
    """List recent threads owned by a user."""
    return get_user_threads(user_id=user_id, limit=limit)


def get_thread_history(user_id: str, thread_id: str) -> dict | None:
    """Get a user's thread history."""
    return get_user_chat_history(user_id=user_id, thread_id=thread_id)


def remove_thread(user_id: str, thread_id: str) -> bool:
    """Delete a user's thread through the repository layer."""
    return delete_user_thread(user_id=user_id, thread_id=thread_id)
