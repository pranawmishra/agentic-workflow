from typing import Literal
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from src.tools import search_tool, weather_tool
# from dotenv import load_dotenv
import os

# tavily_search = TavilySearchResults(max_results=2)

# tavily_search = TavilySearchResults(max_results=2)

class ResearcherNode:
    def __init__(self, llm: ChatCohere):
        self.llm = llm

    def __call__(self, state: MessagesState) -> Command[Literal["validator"]]:

        """
            Research agent node that gathers information using Tavily search.
            Takes the current task state, performs relevant research,
            and returns findings for validation.
        """
        tools = []
    
        research_agent = create_react_agent(
            self.llm,  
            tools=[search_tool, weather_tool],  
            prompt= "You are an Information Specialist with expertise in comprehensive research. Your responsibilities include:\n\n"
                "1. Identifying key information needs based on the query context\n"
                "2. Gathering relevant, accurate, and up-to-date information from reliable sources\n"
                "3. Organizing findings in a structured, easily digestible format\n"
                "4. Citing sources when possible to establish credibility\n"
                "5. Focusing exclusively on information gathering - avoid analysis or implementation\n\n"
                "Provide thorough, factual responses without speculation where information is unavailable."
        )

        result = research_agent.invoke(state)

        for message in result["messages"]:
            if hasattr(message, "tool_calls") and message.tool_calls:
                tools.extend([tool["name"] for tool in message.tool_calls])

        print(f"--- Workflow Transition: Researcher → Validator ---")

        return Command(
            update={
                "tool_calls_made": state.get("tool_calls_made", []) + tools,
                "researcher_output": state.get("researcher_output", []) + [result["messages"][-1].content],
                "messages": [ 
                    HumanMessage(
                        content=result["messages"][-1].content,  
                        name="researcher"  
                    )
                ]
            },
            goto="validator", 
        )