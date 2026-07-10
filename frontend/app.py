"""Athena — Streamlit Chat Interface.

A clean, functional chat UI that communicates with the FastAPI backend.
Features:
- Multi-conversation support with sidebar navigation
- Document upload with status tracking
- Tool usage badges on assistant responses
- Persistent conversation history
"""

import requests
import streamlit as st

# ─── Configuration ─────────────────────────────────────────────────

import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ─── Page Config ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Athena — Intelligent Research Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* Tool badges */
    .tool-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .tool-search_documents {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    .tool-web_search {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
    }
    .tool-arxiv_search {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: white;
    }

    /* Header */
    .athena-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    .athena-header h1 {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .athena-header p {
        color: #888;
        font-size: 0.95rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
    }

    /* Conversation item */
    .conv-item {
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 4px;
        cursor: pointer;
        transition: background 0.2s;
    }
    .conv-item:hover {
        background: rgba(102, 126, 234, 0.15);
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ──────────────────────────────────────────────


def api_call(method: str, endpoint: str, **kwargs) -> dict | list | None:
    """Make an API call to the backend, handling errors gracefully."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.request(method, url, timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the backend. Is it running on http://localhost:8000?")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"⚠️ API error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {str(e)}")
        return None


def render_tool_badges(tools: list[str] | None) -> str:
    """Render HTML badges for the tools used in a response."""
    if not tools:
        return ""

    tool_labels = {
        "search_documents": "📄 Documents",
        "web_search": "🌐 Web Search",
        "arxiv_search": "📚 arXiv",
    }

    badges = []
    for tool in tools:
        label = tool_labels.get(tool, tool)
        css_class = f"tool-{tool}"
        badges.append(f'<span class="tool-badge {css_class}">{label}</span>')

    return " ".join(badges)


# ─── Session State Initialization ─────────────────────────────────

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# ─── Sidebar ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏛️ Athena")
    st.caption("Intelligent Research Assistant")
    st.divider()

    # New Conversation button
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Conversation list
    st.markdown("### 💬 Conversations")
    conversations = api_call("GET", "/conversations")
    if conversations:
        for conv in conversations:
            col1, col2 = st.columns([5, 1])
            with col1:
                is_active = st.session_state.conversation_id == conv["id"]
                button_type = "primary" if is_active else "secondary"
                if st.button(
                    conv["title"][:40] + ("..." if len(conv["title"]) > 40 else ""),
                    key=f"conv_{conv['id']}",
                    use_container_width=True,
                    type=button_type,
                ):
                    st.session_state.conversation_id = conv["id"]
                    # Load messages for this conversation
                    msgs = api_call("GET", f"/conversations/{conv['id']}/messages")
                    if msgs:
                        st.session_state.messages = msgs
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    api_call("DELETE", f"/conversations/{conv['id']}")
                    if st.session_state.conversation_id == conv["id"]:
                        st.session_state.conversation_id = None
                        st.session_state.messages = []
                    st.rerun()

    st.divider()

    # Document Upload
    st.markdown("### 📁 Upload Documents")
    uploaded_file = st.file_uploader(
        "Upload a PDF, TXT, or MD file",
        type=["pdf", "txt", "md"],
        label_visibility="collapsed",
    )
    if uploaded_file and st.button("📤 Process Document", use_container_width=True):
        with st.spinner("Processing document..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            result = api_call("POST", "/upload", files=files)
            if result:
                st.success(
                    f"✅ **{result['filename']}** processed — "
                    f"{result['chunk_count']} chunks indexed"
                )

    # Show uploaded documents
    st.markdown("### 📋 Documents")
    documents = api_call("GET", "/documents")
    if documents:
        for doc in documents:
            status_icon = "✅" if doc["status"] == "completed" else "⏳" if doc["status"] == "processing" else "❌"
            st.caption(f"{status_icon} {doc['filename']} ({doc.get('chunk_count', '?')} chunks)")
    elif documents is not None:
        st.caption("No documents uploaded yet")


# ─── Main Chat Area ───────────────────────────────────────────────

# Header
st.markdown("""
<div class="athena-header">
    <h1>🏛️ Athena</h1>
    <p>Ask me anything — I'll search your documents, the web, or research papers.</p>
</div>
""", unsafe_allow_html=True)

# Display conversation messages
for msg in st.session_state.messages:
    role = msg["role"] if isinstance(msg, dict) else msg.role
    content = msg["content"] if isinstance(msg, dict) else msg.content
    tools = msg.get("tools_used") if isinstance(msg, dict) else getattr(msg, "tools_used", None)

    with st.chat_message(role):
        st.markdown(content)
        if role == "assistant" and tools:
            badges_html = render_tool_badges(tools)
            if badges_html:
                st.markdown(badges_html, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add to local state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call the agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = api_call(
                "POST",
                "/query",
                json={
                    "question": prompt,
                    "conversation_id": st.session_state.conversation_id,
                },
            )

        if response:
            st.markdown(response["answer"])

            # Show tool badges
            if response.get("tools_used"):
                badges_html = render_tool_badges(response["tools_used"])
                if badges_html:
                    st.markdown(badges_html, unsafe_allow_html=True)

            # Update state
            st.session_state.conversation_id = response["conversation_id"]
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "tools_used": response.get("tools_used"),
            })
