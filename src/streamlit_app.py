import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

import streamlit as st
from dotenv import load_dotenv

from client import AgentClient, AgentClientError
from schema import ChatHistory, ChatMessage

APP_TITLE = "AgentHub"
APP_ICON = "〔◉^◉〕"
USER_ID_COOKIE = "user_id"

SAMPLE_QUESTIONS = {
    "chatbot": [
        "What is 2 + 2?",
        "Tell me a fun fact.",
    ],
    "rag-assistant": [
        "List some achievements of Yash Chinchole.",
        "What is the main contribution of the Attention Is All You Need paper?",
        "What is the difference between self-attention and encoder-decoder attention?",
    ],
    "sql": [
        "What are the table names in the Chinook database?",
        "Show me the top 5 customers by total purchase.",
        "List all customers who have placed an order in the past 30 days.",
        "Identify the artist(s) who have released the most albums, along with their names.",
        "Determine the most popular genre(s) in terms of the number of albums and tracks available, and the total sales amount.",
    ],
    "research-assistant": [
        "Provide links to tutorials or documentation for learning Python.",
        "Who won the Nobel Prize in Physics in 2025?",
        "What are the latest trends in artificial intelligence?",
    ],
    "wiki": [
        "What is Retrieval-Augmented Generation (RAG), according to Wikipedia?",
        "Summarize the history of the Internet.",
    ],
    "arxiv": [
        "Find recent Arxiv papers on large language models.",
        "Given an Arxiv paper ID (1706.03762), fetch and summarize the paper's title, authors, abstract, and publication date.",
    ],
}


def _get_or_create_user_id() -> str:
    if USER_ID_COOKIE in st.session_state:
        return st.session_state[USER_ID_COOKIE]
    if USER_ID_COOKIE in st.query_params:
        uid = st.query_params[USER_ID_COOKIE]
        st.session_state[USER_ID_COOKIE] = uid
        return uid
    uid = str(uuid.uuid4())
    st.session_state[USER_ID_COOKIE] = uid
    st.query_params[USER_ID_COOKIE] = uid
    return uid


async def main() -> None:
    st.set_page_config(APP_TITLE, APP_ICON, menu_items={})

    # ---------- Global CSS ----------
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');

    html, body, [class*="css"]  {
        font-family: 'JetBrains Mono', monospace !important;
        background: #1e1e1e !important;
    }

    section.main > div {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 12px;
    }

    [data-testid="stSidebar"] {
        background: #1e1e1e;
        color: #00bff9;
    }

    .stChatMessageUser {
        background: #2a2e3b;
        color: #00bff9;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
    }

    .stChatMessageAI {
        background: #1e352f;
        color: #f1f1f1;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
    }

    [data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0;
    }

    [data-testid="stRadio"] label, 
    [data-testid="stRadio"] div[role="radiogroup"] label {
        color: snow !important;
    }

    textarea[data-testid="stChatInputTextarea"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #00bff9 !important;
    background: #282822 !important;
    border: 1px solid #00bff9 !important;
    border-radius: 8px !important;
    font-size: 16px !important;
    padding: 8px 12px !important;
    }
            
    .stExpander button {
        font-size: 10px !important;
        padding: 4px 6px !important;
    }

    .stExpander {
        font-size: 10px !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    .stExpander > div {
        width: 100% !important;
        max-width: 100% !important;
    }

    .stExpander [data-testid="stExpanderContent"] {
        width: 100% !important;
        max-width: 100% !important;
    }

    </style>
    """,
        unsafe_allow_html=True
    )

    if st.get_option("client.toolbarMode") != "minimal":
        st.set_option("client.toolbarMode", "minimal")
        await asyncio.sleep(0.1)
        st.rerun()

    # ---------- Session init ----------
    user_id = _get_or_create_user_id()
    if "agent_client" not in st.session_state:
        load_dotenv()
        base = os.getenv(
        "AGENT_URL") or f"http://{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 8000)}"
        with st.spinner("Connecting…"):
            st.session_state.agent_client = AgentClient(base_url=base)
    agent_client: AgentClient = st.session_state.agent_client

    if "thread_id" not in st.session_state:
        tid = st.query_params.get("thread_id") or str(uuid.uuid4())
        try:
            hist: ChatHistory = agent_client.get_history(
                thread_id=tid).messages
        except AgentClientError:
            hist = []
        st.session_state.thread_id, st.session_state.messages = tid, hist
    messages: list[ChatMessage] = st.session_state.messages

    # ---------- Sidebar ----------
    with st.sidebar:
        st.header(f"{APP_ICON}  {APP_TITLE}")

        st.markdown(
            "**GitHub** - [Repo Link](https://github.com/yashchinchole/AgentHub)")

        st.caption(
            "AgentHub is a full-stack multi-agent system designed for intelligent querying across diverse data sources. "
            "It supports unstructured data (e.g., PDFs, documents) via a RAG-based agent, structured data (e.g., SQL databases) through a SQL agent, and research assistance using web search, Wikipedia, Arxiv, and a calculator agent for mathematical reasoning."
        )

        AGENT_OPTIONS = {
            "chatbot": "Chatbot",
            "rag-assistant": "RAG Agent",
            "sql": "SQL Agent",
            "research-assistant": "Research Assistant",
            "wiki": "Wikipedia Search",
            "arxiv": "Scientific Paper Search",
        }
        keys, labels = list(AGENT_OPTIONS.keys()), list(AGENT_OPTIONS.values())
        idx_default = keys.index(agent_client.info.default_agent)
        choice_label = st.radio("Choose agent", labels, idx_default)
        agent_client.agent = keys[labels.index(choice_label)]

        if st.button("🗑 New chat", use_container_width=True):
            st.session_state.thread_id, st.session_state.messages = str(uuid.uuid4()), [
            ]
            st.rerun()

        with st.popover("⚙ Settings", use_container_width=True):
            model_idx = agent_client.info.models.index(
                agent_client.info.default_model)
            model = st.selectbox(
                "LLM model", agent_client.info.models, index=model_idx)
            use_stream = st.toggle("Stream tokens", True)
            st.text_input("User ID", user_id, disabled=True)

        st.markdown(
            "[Architecture diagram](https://github.com/yashchinchole/AgentHub/blob/master/media/agent_architecture.png?raw=true)")
        st.caption("Developed by Yash Chinchole")

    # ---------- Welcome on empty chat ----------
    if not messages:
        welcome = {
            "chatbot": "Hello! I'm a simple chatbot. Ask me anything!",
            "rag-assistant": "Hi! I'm Yash Chinchole's assistant. Ask me about my experience and skills. You can also ask questions based on the sample document, the 'Attention Is All You Need' paper!",
            "sql": "Hello! I query the Chinook DB. Ask music/business questions!",
            "research-assistant": "Hi! I'm your web research assistant. Need facts, refs, or maths?",
            "wiki": "Hi! Ask me for concise answers from Wikipedia.",
            "arxiv": "Hi! I can locate & summarise papers from arXiv. Topic?",
        }.get(agent_client.agent, "Hello! I'm an AI agent.")
        st.chat_message("ai").write(welcome)

    # ---------- Replay history ----------
    async def _history() -> AsyncGenerator[ChatMessage, None]:
        for m in messages:
            yield m
    await draw_messages(_history())

    # ---------- Sample questions (after chat history) ----------
    with st.expander("💡 Sample questions", expanded=True):
        sample_qs = SAMPLE_QUESTIONS.get(agent_client.agent, [])
        if sample_qs:
            st.write(
                f"Try these sample questions for the {AGENT_OPTIONS[agent_client.agent]}:")
            for i, q in enumerate(sample_qs):
                if st.button(q, key=f"sample_{agent_client.agent}_{i}"):
                    st.session_state["prefill_question"] = q
                    st.rerun()
        else:
            st.write("No sample questions available for this agent.")

    prefill_text = st.session_state.pop("prefill_question", "")

    try:
        if prefill_text:
            user_input = st.chat_input(
                "Type your message…", value=prefill_text)
        else:
            user_input = st.chat_input("Type your message…")
    except TypeError:
        user_input = st.chat_input("Type your message…")
        if prefill_text:
            user_input = prefill_text

    if user_input:
        messages.append(ChatMessage(type="human", content=user_input))
        st.chat_message("human").write(user_input)
        try:
            if use_stream:
                stream = agent_client.astream(
                    message=user_input,
                    model=model,
                    thread_id=st.session_state.thread_id,
                    user_id=user_id
                )
                await draw_messages(stream, is_new=True)
            else:
                resp = await agent_client.ainvoke(
                    message=user_input,
                    model=model,
                    thread_id=st.session_state.thread_id,
                    user_id=user_id
                )
                messages.append(resp)
                st.chat_message("ai").write(resp.content)
            st.rerun()
        except AgentClientError as e:
            st.error(e)
            st.stop()

    if messages and st.session_state.last_message:
        with st.session_state.last_message:
            await handle_feedback()


async def draw_messages(
    messages_agen: AsyncGenerator[ChatMessage | str, None],
    is_new: bool = False,
) -> None:
    """
    Draws a set of chat messages - either replaying existing messages
    or streaming new ones.

    This function has additional logic to handle streaming tokens and tool calls.
    - Use a placeholder container to render streaming tokens as they arrive.
    - Use a status container to render tool calls. Track the tool inputs and outputs
      and update the status container accordingly.

    The function also needs to track the last message container in session state
    since later messages can draw to the same container. This is also used for
    drawing the feedback widget in the latest chat message.

    Args:
        messages_aiter: An async iterator over messages to draw.
        is_new: Whether the messages are new or not.
    """

    last_message_type = None
    st.session_state.last_message = None

    streaming_content = ""
    streaming_placeholder = None

    while msg := await anext(messages_agen, None):
        if isinstance(msg, str):
            if not streaming_placeholder:
                if last_message_type != "ai":
                    last_message_type = "ai"
                    st.session_state.last_message = st.chat_message("ai")
                with st.session_state.last_message:
                    streaming_placeholder = st.empty()

            streaming_content += msg
            streaming_placeholder.write(streaming_content)
            continue
        if not isinstance(msg, ChatMessage):
            st.error(f"Unexpected message type: {type(msg)}")
            st.write(msg)
            st.stop()

        match msg.type:
            case "human":
                last_message_type = "human"
                st.chat_message("human").write(msg.content)

            case "ai":
                if is_new:
                    st.session_state.messages.append(msg)

                if last_message_type != "ai":
                    last_message_type = "ai"
                    st.session_state.last_message = st.chat_message("ai")

                with st.session_state.last_message:
                    if msg.content:
                        if streaming_placeholder:
                            streaming_placeholder.write(msg.content)
                            streaming_content = ""
                            streaming_placeholder = None
                        else:
                            st.write(msg.content)

                    if msg.tool_calls:
                        call_results = {}
                        for tool_call in msg.tool_calls:
                            status = st.status(
                                f"""Tool Call: {tool_call["name"]}""",
                                state="running" if is_new else "complete",
                            )
                            call_results[tool_call["id"]] = status
                            status.write("Input:")
                            status.write(tool_call["args"])

                        for tool_call in msg.tool_calls:
                            if "transfer_to" in tool_call["name"]:
                                await handle_agent_msgs(messages_agen, call_results, is_new)
                                break
                            tool_result: ChatMessage = await anext(messages_agen)

                            if isinstance(tool_result, str):
                                tool_result = ChatMessage(
                                    type="tool", content=tool_result)

                            if getattr(tool_result, "type", None) != "tool":
                                st.error(
                                    f"Unexpected ChatMessage type: {getattr(tool_result, 'type', tool_result)}")
                                st.write(tool_result)
                                st.stop()

                            if is_new:
                                st.session_state.messages.append(tool_result)
                            if tool_result.tool_call_id:
                                status = call_results[tool_result.tool_call_id]
                            status.write("Output:")
                            status.write(tool_result.content)
                            status.update(state="complete")

            case "tool":
                # Handle tool messages that might come as top-level messages
                if is_new:
                    st.session_state.messages.append(msg)

                status = st.status(
                    f"Tool Output",
                    state="complete",
                )
                status.write("Output:")
                status.write(msg.content)
                status.update(state="complete")

            case _:
                st.error(f"Unexpected ChatMessage type: {msg.type}")
                st.write(msg)
                st.stop()


async def handle_feedback() -> None:
    """Draws a feedback widget and records feedback from the user."""

    if "last_feedback" not in st.session_state:
        st.session_state.last_feedback = (None, None)

    latest_run_id = st.session_state.messages[-1].run_id
    feedback = st.feedback("stars", key=latest_run_id)

    if feedback is not None and (latest_run_id, feedback) != st.session_state.last_feedback:
        normalized_score = (feedback + 1) / 5.0

        agent_client: AgentClient = st.session_state.agent_client
        try:
            await agent_client.acreate_feedback(
                run_id=latest_run_id,
                key="human-feedback-stars",
                score=normalized_score,
                kwargs={"comment": "In-line human feedback"},
            )
        except AgentClientError as e:
            st.error(f"Error recording feedback: {e}")
            st.stop()
        st.session_state.last_feedback = (latest_run_id, feedback)
        st.toast("Feedback recorded", icon=":material/reviews:")


async def handle_agent_msgs(messages_agen, call_results, is_new):
    """
    This function segregates agent output into a status container.
    It handles all messages after the initial tool call message
    until it reaches the final AI message.
    """
    nested_popovers = {}
    first_msg = await anext(messages_agen)
    if is_new:
        st.session_state.messages.append(first_msg)
    status = call_results.get(getattr(first_msg, "tool_call_id", None))
    if status and first_msg.content:
        status.write(first_msg.content)
    while True:
        finish_reason = getattr(
            first_msg, "response_metadata", {}).get("finish_reason")
        if finish_reason is not None and finish_reason != "tool_calls":
            if status:
                status.update(state="complete")
            break
        sub_msg = await anext(messages_agen)
        if is_new:
            st.session_state.messages.append(sub_msg)

        if sub_msg.type == "tool" and sub_msg.tool_call_id in nested_popovers:
            popover = nested_popovers[sub_msg.tool_call_id]
            popover.write("**Output:**")
            popover.write(sub_msg.content)
            first_msg = sub_msg
            continue
        if status:
            if sub_msg.content:
                status.write(sub_msg.content)
            if hasattr(sub_msg, "tool_calls") and sub_msg.tool_calls:
                for tc in sub_msg.tool_calls:
                    popover = status.popover(f"{tc['name']}", icon="🛠️")
                    popover.write(f"**Tool:** {tc['name']}")
                    popover.write("**Input:**")
                    popover.write(tc["args"])
                    nested_popovers[tc["id"]] = popover
        first_msg = sub_msg

if __name__ == "__main__":
    asyncio.run(main())
