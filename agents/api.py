import asyncio
import os
import json
from typing import Annotated, Optional, List, Sequence
from typing_extensions import TypedDict

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from langchain.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI

from firecrawl import FirecrawlApp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from .models import AgentLog 
import nest_asyncio
nest_asyncio.apply()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=GEMINI_API_KEY
)

class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    keywords: Optional[List[str]]

@tool
def Keyword_extractor(state: AgentState) -> AgentState:
    """Extract keywords from user input"""
    prompt = SystemMessage(
        content="You are a helpful assistant. Extract search keywords..."
    )
    response = model.invoke([prompt] + state["messages"])
    try:
        keywords = json.loads(response.content)
        if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
            state["keywords"] = keywords
        else:
            state["keywords"] = ["[Invalid format]"]
    except json.JSONDecodeError:
        state["keywords"] = ["[Parsing failed]"]
    return state

server_params = StdioServerParameters(
    command="npx",
    env={"FIRECRAWL_API_KEY": FIRECRAWL_API_KEY},
    args=["firecrawl-mcp"]
)

async def agent_main(state: AgentState) -> AgentState:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            search_query = " ".join(state.get("keywords", []))
            system_msg = {"role": "system", "content": "You're a helpful AI agent..."}
            user_msg = {"role": "user", "content": f"Search and summarize: {state['messages']} {search_query}"}

            messages = [system_msg, user_msg]
            result = await agent.ainvoke({"messages": messages})
            final_response = result["messages"][-1].content
            state["messages"].append(AIMessage(content=final_response))
            return state

async def run_agent_logic(user_input: str):
    state: AgentState = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    # 🔥 FIXED: Must pass dict with key 'state'
    state = await Keyword_extractor.ainvoke({"state": state})

    state = await agent_main(state)
    
    return {
        "keywords": state.get("keywords", []),
        "response": state["messages"][-1].content
    }
