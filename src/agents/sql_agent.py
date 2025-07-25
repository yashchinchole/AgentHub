from pathlib import Path
from langchain.chat_models import init_chat_model
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent
from langchain import hub

CHINOOK_PATH = Path(__file__).parents[2] / "data" / "Chinook.db"
DB_URI = f"sqlite:///{CHINOOK_PATH}"


def build():
    llm = init_chat_model("openai:gpt-4o-mini", temperature=0)

    db = SQLDatabase.from_uri(DB_URI)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
    system_msg = prompt_template.format(dialect="SQLite", top_k=5)

    agent = create_react_agent(
        llm,
        toolkit.get_tools(),
        prompt=system_msg,
    )
    return agent
