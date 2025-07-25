from dataclasses import dataclass

from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import Pregel

from agents.chatbot import chatbot
from agents.rag_assistant import rag_assistant
from agents.research_assistant import research_assistant
from agents.sql_agent import build as build_sql_agent
from agents.wikipedia_agent import wiki_agent
from agents.arxiv_agent import arxiv_scholar
from schema import AgentInfo


DEFAULT_AGENT = "chatbot"

AgentGraph = CompiledStateGraph | Pregel


@dataclass
class Agent:
    description: str
    graph: AgentGraph


agents: dict[str, Agent] = {
    "chatbot": Agent(description="A simple chatbot.", graph=chatbot),
    "research-assistant": Agent(
        description="A research assistant with web search and calculator.", graph=research_assistant
    ),
    "rag-assistant": Agent(
        description="A RAG assistant with access to information in a database.", graph=rag_assistant
    ),
    "sql": Agent(
        description="A SQL assistant agent querying the Chinook database.",
        graph=build_sql_agent()
    ),
    "wiki": Agent(description="A Wikipedia research assistant.", graph=wiki_agent),
    "arxiv": Agent(description="ArXiv Scholar: scientific paper search agent.", graph=arxiv_scholar),
}


def get_agent(agent_id: str) -> AgentGraph:
    return agents[agent_id].graph


def get_all_agent_info() -> list[AgentInfo]:
    return [
        AgentInfo(key=agent_id, description=agent.description) for agent_id, agent in agents.items()
    ]
