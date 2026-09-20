from datetime import datetime, timezone
import uuid
import bcrypt
from .database_config import db

users_collection = db["users"]

# Create a unique index on 'username' and 'email' so duplicates are impossible
users_collection.create_index("username", unique=True)
users_collection.create_index("email", unique=True)


def register_user(username: str, email: str, plaintext_password: str) -> str:
    """Hashes the password and saves a new user profile to the database."""
    # Convert inputs to lowercase to prevent casing lookup errors
    username_clean = username.strip().lower()
    email_clean = email.strip().lower()

    # Hash the password securely using bcrypt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plaintext_password.encode("utf-8"), salt)

    user_id = str(uuid.uuid4())  # Generate a permanent, unique user ID

    new_user = {
        "_id": user_id,
        "username": username_clean,
        "email": email_clean,
        "password_hash": hashed_password,  # Storing the securely encrypted hash
        "display_name": username,  # Keeps original casing for the UI
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc),
    }

    try:
        users_collection.insert_one(new_user)
        print(f"🎉 User '{username}' registered successfully! ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"❌ Registration failed: Username or Email already exists.")
        return None


def verify_user_login(username_or_email: str, plaintext_password: str) -> dict:
    """Verifies user credentials. Returns user profile data if valid, else None."""
    lookup_identifier = username_or_email.strip().lower()

    # Look up the user by either username or email
    user = users_collection.find_one(
        {
            "$or": [
                {"username": lookup_identifier},
                {"email": lookup_identifier},
            ]
        }
    )

    if not user:
        print("❌ Login failed: User not found.")
        return None

    # Check if the entered password matches the stored hash
    if bcrypt.checkpw(plaintext_password.encode("utf-8"), user["password_hash"]):
        # Update last login timestamp
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc)}},
        )
        print(f"🔓 Login successful! Welcome back, {user['display_name']}.")

        # Return user details (excluding the raw password hash for safety)
        return {
            "user_id": user["_id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "email": user["email"],
        }
    else:
        print("❌ Login failed: Incorrect password.")
        return None


# ==========================================
# 🚀 SIMULATION RUN
# ==========================================
if __name__ == "__main__":
    print("--- Testing User Registration ---")
    # 1. Simulate a new user signing up
    user_id = register_user(
        username="JohnDoe",
        email="john@example.com",
        plaintext_password="SuperSecretPassword123",
    )

    # Try registering the exact same user again to test unique constraints
    print("\n--- Testing Duplicate Registration (Should Fail) ---")
    register_user(
        username="johndoe",
        email="john@example.com",
        plaintext_password="AnotherPassword",
    )

    print("\n--- Testing Login System ---")
    # 2. Simulate trying to log in with a wrong password
    verify_user_login("JohnDoe", "WrongPassword!!")

    # 3. Simulate a successful login using email
    logged_in_user = verify_user_login(
        "john@example.com", "SuperSecretPassword123"
    )

    if logged_in_user:
        print(f"\nSession active for User ID: {logged_in_user['user_id']}")
