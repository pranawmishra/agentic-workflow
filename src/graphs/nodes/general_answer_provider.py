from langchain_cohere import ChatCohere
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from typing import Literal
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

class GeneralAnswerProviderNode:
    def __init__(self, llm: ChatCohere):
        self.llm = llm

    def __call__(self, state: MessagesState) -> Command[Literal["__end__"]]:

        general_answer_agent = create_react_agent(
            self.llm,
            tools=[],
            prompt=(
                "You are a general answer provider. Focus on providing a general answer to the user's query when the task is not clear or the user's request is not possible to complete or the user query does not require any of the other agents."
            )
        )

        response = general_answer_agent.invoke(state)

        return Command(
            update={
                "messages": [
                    AIMessage(content=response["messages"][-1].content, name="general_answer_provider")
                ]
            },
            goto=END,
        )