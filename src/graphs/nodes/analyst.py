from typing import Literal
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool

class AnalystNode:
    def __init__(self, llm: ChatCohere):
        self.llm = llm
        self.python_repl_tool = PythonREPLTool()

    def __call__(self, state: MessagesState) -> Command[Literal["validator"]]:
        tools = []
        try:

            analyst_agent = create_react_agent(
                self.llm,
                tools=[self.python_repl_tool],
                prompt=(
                    "You are a coder and analyst. Focus on mathematical calculations, analyzing, solving math questions, "
                    "and executing code. Handle technical problem-solving and data tasks."
                )
            )

            results = analyst_agent.invoke(state)

            for message in results["messages"]:
                if hasattr(message, "tool_calls") and message.tool_calls:
                    tools.extend([tool["name"] for tool in message.tool_calls])


            print(f"--- Workflow Transition: Analyst → Validator ---")

            return Command(
                update={
                    "tool_calls_made": state.get("tool_calls_made", []) + tools,
                    "analyst_output": state.get("analyst_output", []) + [results["messages"][-1].content],
                    "messages": [
                        HumanMessage(content=results["messages"][-1].content, name="analyst")
                    ]
                },
                goto="validator",
            )
        except Exception as e:
            print(f"Error in AnalystNode: {e}")
            return Command(
                update={
                    "messages": [
                        HumanMessage(content=f"Error: {str(e)}", name="analyst")
                    ]
                },
                goto="validator",
            )