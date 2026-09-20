import uuid

import extra_streamlit_components as stx
import requests
import streamlit as st


USER_COOKIE_NAME = "chat_user_id"


def ensure_user_session(api_url: str) -> bool:
    """Load user_id from a browser cookie or create a guest user through the API."""
    if "user_id" in st.session_state:
        return True

    cookie_user_id = st.context.cookies.get(USER_COOKIE_NAME)
    if cookie_user_id:
        st.session_state.user_id = cookie_user_id
        return True

    if "guest_credentials" not in st.session_state:
        guest_id = uuid.uuid4().hex[:8]
        st.session_state.guest_credentials = {
            "username": f"guest_{guest_id}",
            "email": f"guest_{guest_id}@local.chat",
            "password": uuid.uuid4().hex,
        }

    credentials = st.session_state.guest_credentials
    response = requests.post(
        f"{api_url}/users/register",
        json=credentials,
        timeout=10,
    )
    if response.status_code == 409:
        response = requests.post(
            f"{api_url}/users/login",
            json={
                "username_or_email": credentials["username"],
                "password": credentials["password"],
            },
            timeout=10,
        )
    response.raise_for_status()

    user_id = response.json()["user_id"]
    cookie_manager = stx.CookieManager(key="chat-user-cookie")
    cookie_manager.set(
        USER_COOKIE_NAME,
        user_id,
        max_age=60 * 60 * 24 * 30,
        same_site="lax",
    )
    st.session_state.user_id = user_id
    st.rerun()
    return True
