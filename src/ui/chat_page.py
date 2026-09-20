import json
import base64
from html import escape

import requests
import streamlit as st

from config import BACKEND_STREAM_URL
from ui.file_context import extract_file_text
from ui.summary_export import create_pdf, create_pptx
from ui.user_session import ensure_user_session

BACKEND_API_URL = BACKEND_STREAM_URL.rsplit("/stream", 1)[0] + "/api"
BACKEND_ROOT_URL = BACKEND_STREAM_URL.rsplit("/stream", 1)[0]


def initialize_chat_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "file_context" not in st.session_state:
        st.session_state.file_context = ""
    if "file_name" not in st.session_state:
        st.session_state.file_name = None
    if "summary_text" not in st.session_state:
        st.session_state.summary_text = None
    if "summary_pdf" not in st.session_state:
        st.session_state.summary_pdf = None
    if "summary_pptx" not in st.session_state:
        st.session_state.summary_pptx = None
    if "summary_format" not in st.session_state:
        st.session_state.summary_format = None


def create_new_chat(
    title: str = "New chat", clear_file_context: bool = True
) -> None:
    response = requests.post(
        f"{BACKEND_API_URL}/threads",
        json={
            "user_id": st.session_state.user_id,
            "title": title,
            "is_guest": True,
        },
        timeout=10,
    )
    response.raise_for_status()
    st.session_state.thread_id = response.json()["thread_id"]
    st.session_state.messages = []
    st.session_state.summary_text = None
    st.session_state.summary_pdf = None
    st.session_state.summary_pptx = None
    st.session_state.summary_format = None
    if clear_file_context:
        st.session_state.file_context = ""
        st.session_state.file_name = None


def fetch_recent_chats() -> list[dict]:
    response = requests.get(
        f"{BACKEND_API_URL}/threads",
        params={"user_id": st.session_state.user_id, "limit": 20},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def open_chat(thread_id: str) -> None:
    response = requests.get(
        f"{BACKEND_API_URL}/threads/{thread_id}",
        params={"user_id": st.session_state.user_id},
        timeout=10,
    )
    response.raise_for_status()
    thread = response.json()
    st.session_state.thread_id = thread["thread_id"]
    st.session_state.messages = [
        {"role": message["role"], "content": message["content"]}
        for message in thread.get("messages", [])
    ]


def remove_chat(thread_id: str) -> None:
    response = requests.delete(
        f"{BACKEND_API_URL}/threads/{thread_id}",
        params={"user_id": st.session_state.user_id},
        timeout=10,
    )
    response.raise_for_status()
    if st.session_state.thread_id == thread_id:
        st.session_state.thread_id = None
        st.session_state.messages = []


def generate_summary(output_format: str) -> None:
    if not st.session_state.messages:
        st.warning("Start a conversation before generating a summary.")
        return

    conversation_messages = list(st.session_state.messages)
    if conversation_messages and conversation_messages[-1]["role"] == "user":
        if requested_summary_format(conversation_messages[-1]["content"]):
            conversation_messages.pop()

    refusal_markers = (
        "i cannot directly generate",
        "i can't directly generate",
        "provide you with a python script",
        "pip install fpdf",
    )
    conversation_messages = [
        message
        for message in conversation_messages
        if not (
            message["role"] == "assistant"
            and any(
                marker in message["content"].lower()
                for marker in refusal_markers
            )
        )
    ]
    if not conversation_messages:
        st.warning("Have a conversation before requesting a summary.")
        return

    response = requests.post(
        f"{BACKEND_ROOT_URL}/generate",
        json={
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a document summarizer. Produce the actual summary "
                        "content only from the conversation. Do not repeat export "
                        "requests or refusal messages. Do not say you cannot create "
                        "files and do not discuss limitations. Include a title, key "
                        "points, decisions, and action items when available."
                    ),
                },
                *conversation_messages,
            ]
        },
        timeout=60,
    )
    response.raise_for_status()
    summary = response.json()["response"]
    st.session_state.summary_text = summary
    st.session_state.summary_format = output_format
    st.session_state.summary_pdf = (
        create_pdf(summary) if output_format == "pdf" else None
    )
    st.session_state.summary_pptx = (
        create_pptx(summary) if output_format == "pptx" else None
    )


def requested_summary_format(prompt: str) -> str | None:
    text = prompt.lower()
    has_export_intent = any(
        term in text
        for term in ("summary", "summarize", "generate", "create", "make", "export", "download")
    )
    if not has_export_intent:
        return None
    if "pdf" in text:
        return "pdf"
    if any(term in text for term in ("ppt", "pptx", "powerpoint")):
        return "pptx"
    return None


def render_summary_preview() -> None:
    if not st.session_state.summary_text:
        return

    st.divider()
    st.subheader("Generated summary")
    st.markdown(st.session_state.summary_text)

    if st.session_state.summary_format == "pdf" and st.session_state.summary_pdf:
        st.caption("PDF preview")
        pdf_data = base64.b64encode(st.session_state.summary_pdf).decode("ascii")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{pdf_data}" '
            'width="100%" height="560" style="border:1px solid #444;" '
            'title="PDF summary preview"></iframe>',
            unsafe_allow_html=True,
        )

    if st.session_state.summary_format == "pptx" and st.session_state.summary_pptx:
        st.caption("PowerPoint preview")
        st.info(
            "PowerPoint preview is shown as slide text. Download the PPTX to open it in PowerPoint."
        )
        for slide_number, slide_text in enumerate(
            st.session_state.summary_text.split("\n"), 1
        ):
            if slide_text.strip():
                st.markdown(f"**Slide {slide_number}:** {slide_text}")

    if st.session_state.summary_format == "pdf":
        st.download_button(
            "Download PDF",
            data=st.session_state.summary_pdf,
            file_name="chat-summary.pdf",
            mime="application/pdf",
            key="summary-pdf-main",
        )
    elif st.session_state.summary_format == "pptx":
        st.download_button(
            "Download PowerPoint",
            data=st.session_state.summary_pptx,
            file_name="chat-summary.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="summary-pptx-main",
        )


def render_sidebar() -> None:
    with st.sidebar:
        if st.button("+  New chat", use_container_width=True):
            try:
                create_new_chat()
                st.rerun()
            except requests.exceptions.RequestException as error:
                st.error(f"Unable to create chat: {error}")

        st.divider()
        st.caption("Recent chats")
        try:
            recent_chats = fetch_recent_chats()
            if not recent_chats:
                st.caption("No chats yet")
            for chat in recent_chats:
                label = chat["title"].strip() or "New chat"
                chat_column, remove_column = st.columns([5, 1])
                with chat_column:
                    if st.button(
                        label[:36],
                        key=f"chat-{chat['thread_id']}",
                        use_container_width=True,
                    ):
                        try:
                            open_chat(chat["thread_id"])
                            st.rerun()
                        except requests.exceptions.RequestException as error:
                            st.error(f"Unable to open chat: {error}")
                with remove_column:
                    if st.button(
                        "x",
                        key=f"remove-{chat['thread_id']}",
                        help="Remove this chat",
                    ):
                        try:
                            remove_chat(chat["thread_id"])
                            st.rerun()
                        except requests.exceptions.RequestException as error:
                            st.error(f"Unable to remove chat: {error}")
        except requests.exceptions.RequestException as error:
            st.error(f"Unable to load recent chats: {error}")

def render_messages() -> None:
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])


def render_message(role: str, content: str):
    """Render user prompts as right bubbles and assistant responses on the left."""
    if role == "user":
        _, message_column, _ = st.columns([1, 4, 2])
        with message_column:
            st.markdown(
                "<div style='display:flex;justify-content:flex-end;'>"
                "<div style='background:#2f2f2f;color:#ffffff;"
                "padding:10px 16px;border-radius:18px;max-width:100%;"
                "overflow-wrap:anywhere;line-height:1.5;'>"
                f"{escape(content)}"
                "</div></div>",
                unsafe_allow_html=True,
            )
        return
    else:
        message_column, _ = st.columns([6, 1])

    with message_column:
        st.markdown(content)


def stream_response(prompt: str) -> None:
    if st.session_state.thread_id is None:
        try:
            create_new_chat(
                title=prompt[:50] or "New chat",
                clear_file_context=False,
            )
        except requests.exceptions.RequestException as error:
            st.error(f"Unable to create chat: {error}")
            return

    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message("user", prompt)

    output_format = requested_summary_format(prompt)
    if output_format:
        try:
            generate_summary(output_format)
            st.rerun()
        except requests.exceptions.RequestException as error:
            st.error(f"Unable to generate summary file: {error}")
        return

    response_column, _ = st.columns([6, 1])
    with response_column:
        response_box = st.empty()
    full_response = ""
    stream_error = None
    try:
        llm_messages = list(st.session_state.messages)
        if st.session_state.file_context:
            llm_messages.insert(
                0,
                {
                    "role": "system",
                    "content": (
                        "Answer questions about the uploaded file using only the "
                        "following file context when relevant.\n\n"
                        f"File: {st.session_state.file_name}\n"
                        f"{st.session_state.file_context}"
                    ),
                },
            )

        response = requests.post(
            f"{BACKEND_API_URL}/chat/stream",
            json={
                "user_id": st.session_state.user_id,
                "thread_id": st.session_state.thread_id,
                "messages": llm_messages,
            },
            stream=True,
            timeout=60,
        )
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                if chunk.get("thread_id"):
                    st.session_state.thread_id = chunk["thread_id"]
                if chunk.get("error"):
                    stream_error = chunk["error"]
                    break
                full_response += chunk.get("content", "")
                response_box.markdown(full_response + "▌")
            except json.JSONDecodeError:
                continue
        if stream_error:
            st.error(f"LLM request failed: {stream_error}")
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
    except requests.exceptions.RequestException as error:
        st.error(f"Backend request failed: {error}")


def render_chat_page() -> None:
    st.set_page_config(page_title="Live AI Chat", page_icon="💬", layout="wide")
    initialize_chat_state()
    try:
        ensure_user_session(BACKEND_API_URL)
    except requests.exceptions.RequestException as error:
        st.error(f"Unable to create user: {error}")
        st.stop()
    render_sidebar()

    render_messages()
    render_summary_preview()

    prompt_value = st.chat_input(
        "Ask anything",
        accept_file=True,
        file_type=[
            "txt",
            "md",
            "csv",
            "json",
            "py",
            "yaml",
            "yml",
            "html",
            "css",
            "js",
            "ts",
            "pdf",
            "docx",
        ],
    )
    prompt = prompt_value
    if not isinstance(prompt_value, str) and prompt_value is not None:
        prompt = prompt_value.text
        uploaded_files = prompt_value.files
        if uploaded_files:
            uploaded_file = uploaded_files[0]
            try:
                st.session_state.file_context = extract_file_text(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                )[:30000]
                st.session_state.file_name = uploaded_file.name
            except (ValueError, ImportError) as error:
                st.session_state.file_context = ""
                st.session_state.file_name = None
                st.error(str(error))
    if prompt:
        stream_response(prompt)
