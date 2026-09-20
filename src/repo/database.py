from datetime import datetime, timezone
import uuid
from typing import Any

from .database_config import client, db


def get_collection(collection_name: str) -> Any:
    """Return a collection backed by the shared MongoDB client."""
    return db[collection_name]


threads_collection = get_collection("threads")


def create_chat_thread(user_id: str, title: str, is_guest: bool = False) -> str:
    """Creates a new conversation thread document in the database."""
    thread_id = str(uuid.uuid4())  # Generate a unique ID for this chat thread

    new_thread = {
        "_id": thread_id,
        "user_id": user_id,
        "is_guest": is_guest,
        "title": title,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "messages": [],
    }

    threads_collection.insert_one(new_thread)
    print(f"🎉 New thread created successfully! ID: {thread_id}")
    return thread_id


def add_message_to_thread(thread_id: str, role: str, content: str):
    """Appends a new message (either from 'user' or 'assistant') to the thread's message array."""
    message_data = {
        "message_id": str(uuid.uuid4()),
        "role": role,  # Must be 'user' or 'assistant'
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    }

    # $push appends the message to the array; $set updates the timestamp
    threads_collection.update_one(
        {"_id": thread_id},
        {
            "$push": {"messages": message_data},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    print(f"✅ Added {role} message to thread {thread_id}")


def get_chat_history(thread_id: str) -> dict:
    """Retrieves the complete thread document, including all messages."""
    return threads_collection.find_one({"_id": thread_id})


def get_user_threads(user_id: str, limit: int = 20) -> list[dict]:
    """Return the most recently updated threads owned by a user."""
    return list(
        threads_collection.find(
            {"user_id": user_id},
            {"messages": 0},
        )
        .sort("updated_at", -1)
        .limit(limit)
    )


def get_user_chat_history(user_id: str, thread_id: str) -> dict | None:
    """Retrieve a thread only when it belongs to the requested user."""
    return threads_collection.find_one(
        {"_id": thread_id, "user_id": user_id}
    )


def delete_user_thread(user_id: str, thread_id: str) -> bool:
    """Delete a thread only when it belongs to the requested user."""
    result = threads_collection.delete_one(
        {"_id": thread_id, "user_id": user_id}
    )
    return result.deleted_count == 1


# ==========================================
# 🚀 SIMULATION RUN
# ==========================================
if __name__ == "__main__":
    print("--- Testing Registered User Scenario ---")
    # Simulate a logged-in user starting a chat
    registered_user = "johndoe123"
    user_thread_id = create_chat_thread(
        user_id=registered_user, title="Python coding help", is_guest=False
    )

    # Simulate the chat exchange
    add_message_to_thread(user_thread_id, "user", "How do I use MongoDB?")
    add_message_to_thread(
        user_thread_id,
        "assistant",
        "You can use the pymongo library in Python!",
    )

    print("\n--- Testing Guest User Scenario ---")
    # Simulate an anonymous guest visiting the site (generate a temporary guest ID)
    guest_user_id = f"guest_{uuid.uuid4().hex[:8]}"
    guest_thread_id = create_chat_thread(
        user_id=guest_user_id, title="Quick testing session", is_guest=True
    )

    add_message_to_thread(
        guest_thread_id, "user", "Does this save guest chats?"
    )
    add_message_to_thread(
        guest_thread_id, "assistant", "Yes, it saves them under a guest flag."
    )

    # Verify data by printing out the full history of the first chat
    print("\n--- Verifying Stored Data ---")
    history = get_chat_history(user_thread_id)
    print(f"Chat Title: {history['title']}")
    print(f"Total Messages Saved: {len(history['messages'])}")
