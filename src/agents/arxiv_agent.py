from datetime import datetime
from typing import Literal

from langchain_community.tools import ArxivQueryRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda, RunnableSerializable
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.managed import RemainingSteps
from langgraph.prebuilt import ToolNode

from agents.llama_guard import LlamaGuard, LlamaGuardOutput, SafetyAssessment
from core import get_model, settings


class AgentState(MessagesState, total=False):
    safety: LlamaGuardOutput
    remaining_steps: RemainingSteps


arxiv_tool = ArxivQueryRun(name="Arxiv")
tools = [arxiv_tool]


current_date = datetime.now().strftime("%B %d, %Y")
instructions = f"""
You are ArXiv Scholar, a scientific research assistant. Use the Arxiv tool to find and summarize recent papers and results from arXiv.org.
Today's date is {current_date}.

NOTE: THE USER CAN'T SEE THE TOOL RESPONSE.

Provide answers with relevant paper titles, abstracts, and markdown-formatted arXiv links.
"""


def wrap_model(model: BaseChatModel) -> RunnableSerializable[AgentState, AIMessage]:
    """Bind the tools and prepend system instructions to the messages."""
    bound_model = model.bind_tools(tools)
    preprocessor = RunnableLambda(
        lambda state: [SystemMessage(
            content=instructions)] + state["messages"],
        name="StateModifier",
    )
    return preprocessor | bound_model


def format_safety_message(safety: LlamaGuardOutput) -> AIMessage:
    """Format a message to notify about unsafe content detected."""
    content = (
        f"This conversation was flagged for unsafe content: {', '.join(safety.unsafe_categories)}"
    )
    return AIMessage(content=content)


async def acall_model(state: AgentState, config: RunnableConfig) -> AgentState:
    """Call the model with the current state and run safety guard on the model output."""
    m = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    model_runnable = wrap_model(m)
    response = await model_runnable.ainvoke(state, config)

    llama_guard = LlamaGuard()
    safety_output = await llama_guard.ainvoke("Agent", state["messages"] + [response])
    if safety_output.safety_assessment == SafetyAssessment.UNSAFE:
        return {"messages": [format_safety_message(safety_output)], "safety": safety_output}

    if state.get("remaining_steps", 10) < 2 and getattr(response, "tool_calls", None):
        return {
            "messages": [
                AIMessage(
                    id=getattr(response, "id", ""),
                    content="Sorry, need more steps to process this request.",
                )
            ],
            "safety": safety_output,
        }

    return {"messages": [response], "safety": safety_output}


async def llama_guard_input(state: AgentState, config: RunnableConfig) -> AgentState:
    """Run safety guard on user input before model invocation."""
    llama_guard = LlamaGuard()
    safety_output = await llama_guard.ainvoke("User", state["messages"])
    return {"safety": safety_output, "messages": []}


async def block_unsafe_content(state: AgentState, config: RunnableConfig) -> AgentState:
    """Block and respond with safety warning if content flagged unsafe."""
    safety: LlamaGuardOutput = state["safety"]
    return {"messages": [format_safety_message(safety)]}


agent = StateGraph(AgentState)
agent.add_node("model", acall_model)
agent.add_node("tools", ToolNode(tools))
agent.add_node("guard_input", llama_guard_input)
agent.add_node("block_unsafe_content", block_unsafe_content)
agent.set_entry_point("guard_input")


def check_safety(state: AgentState) -> Literal["unsafe", "safe"]:
    safety: LlamaGuardOutput = state["safety"]
    match safety.safety_assessment:
        case SafetyAssessment.UNSAFE:
            return "unsafe"
        case _:
            return "safe"


agent.add_conditional_edges(
    "guard_input",
    check_safety,
    {"unsafe": "block_unsafe_content", "safe": "model"},
)
agent.add_edge("block_unsafe_content", END)
agent.add_edge("tools", "model")


def pending_tool_calls(state: AgentState) -> Literal["tools", "done"]:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last_message)}")
    if last_message.tool_calls:
        return "tools"
    return "done"


agent.add_conditional_edges(
    "model",
    pending_tool_calls,
    {"tools": "tools", "done": END},
)


arxiv_scholar = agent.compile()
