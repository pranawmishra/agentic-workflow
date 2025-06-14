from typing import Literal
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool

class CodeNode:
    def __init__(self, llm: ChatAnthropic):
        self.llm = llm
        self.python_repl_tool = PythonREPLTool()

    def __call__(self, state: MessagesState) -> Command[Literal["validator"]]:

        code_agent = create_react_agent(
            self.llm,
            tools=[self.python_repl_tool],
            prompt=(
                "You are a coder and analyst. Focus on mathematical calculations, analyzing, solving math questions, "
                "and executing code. Handle technical problem-solving and data tasks."
            )
        )

        result = code_agent.invoke(state)

        print(f"--- Workflow Transition: Coder → Validator ---")

        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name="coder")
                ]
            },
            goto="validator",
        )