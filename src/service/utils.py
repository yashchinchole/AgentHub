from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)

from schema import ChatMessage


def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    """Convert message content to string, handling various content formats."""
    try:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content)

        text: list[str] = []
        for content_item in content:
            if isinstance(content_item, str):
                text.append(content_item)
                continue
            if isinstance(content_item, dict) and content_item.get("type") == "text":
                text.append(content_item.get("text", ""))
            elif content_item is not None:
                # Fallback for other content types
                text.append(str(content_item))
        return "".join(text)
    except Exception as e:
        # Log the error and return a fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Failed to convert message content to string: {e}, content: {content}")
        return str(content) if content is not None else ""


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Create a ChatMessage from a LangChain message."""
    try:
        match message:
            case HumanMessage():
                human_message = ChatMessage(
                    type="human",
                    content=convert_message_content_to_string(message.content),
                )
                return human_message
            case AIMessage():
                ai_message = ChatMessage(
                    type="ai",
                    content=convert_message_content_to_string(message.content),
                )
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    ai_message.tool_calls = message.tool_calls
                if hasattr(message, 'response_metadata') and message.response_metadata:
                    ai_message.response_metadata = message.response_metadata
                return ai_message
            case ToolMessage():
                tool_message = ChatMessage(
                    type="tool",
                    content=convert_message_content_to_string(message.content),
                    tool_call_id=getattr(message, 'tool_call_id', None),
                )
                return tool_message
            case LangchainChatMessage():
                if hasattr(message, 'role') and message.role == "custom":
                    custom_message = ChatMessage(
                        type="custom",
                        content="",
                        custom_data=message.content[0] if isinstance(
                            message.content, list) and len(message.content) > 0 else {},
                    )
                    return custom_message
                else:
                    # Fallback for other LangchainChatMessage types
                    return ChatMessage(
                        type="ai",
                        content=convert_message_content_to_string(
                            message.content),
                    )
            case _:
                # Fallback for unknown message types
                return ChatMessage(
                    type="ai",
                    content=convert_message_content_to_string(message.content),
                )
    except Exception as e:
        # Log the error and return a fallback message
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Failed to parse message {type(message)}: {e}, falling back to basic message")
        return ChatMessage(
            type="ai",
            content=str(message.content) if hasattr(
                message, 'content') else "Message parsing error",
        )


def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
    """Remove tool calls from content."""
    try:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content)

        return [
            content_item
            for content_item in content
            if isinstance(content_item, str) or (isinstance(content_item, dict) and content_item.get("type") != "tool_use")
        ]
    except Exception as e:
        # Log the error and return a fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Failed to remove tool calls from content: {e}, content: {content}")
        return str(content) if content is not None else ""
