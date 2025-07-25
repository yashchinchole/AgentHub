from agents import DEFAULT_AGENT, get_agent
import asyncio
from typing import cast
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState
from langgraph.graph.state import CompiledStateGraph

load_dotenv()


agent = cast(CompiledStateGraph, get_agent(DEFAULT_AGENT))


async def main() -> None:
    inputs: MessagesState = {
        "messages": [HumanMessage("Find me a recipe for chocolate chip cookies")]
    }
    result = await agent.ainvoke(
        input=inputs,
        config=RunnableConfig(configurable={"thread_id": uuid4()}),
    )
    result["messages"][-1].pretty_print()

    agent.get_graph().draw_png("agent_diagram.png")

if __name__ == "__main__":
    asyncio.run(main())
