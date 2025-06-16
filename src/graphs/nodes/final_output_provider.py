from typing import Literal
from langgraph.graph import END, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

# System prompt providing clear instructions to the validator agent
system_prompt = '''
    Your task is to provide the final output of the workflow.
    Specifically, you must:
    - Review the user's question (the first message in the workflow).
    - Review the answer (the last message in the workflow).
    
    - Provide the final output of the workflow.
'''

class FinalOutputProvider(BaseModel):
    final_output: str = Field(
        description="The final output of the workflow."
    )

class FinalOutputProviderNode:
    def __init__(self, llm: ChatAnthropic):
        self.llm = llm

    def __call__(self, state: MessagesState) -> Command[Literal["__end__"]]:

        agent_answer = state["messages"][-2].content

        print(f"--- Workflow Transition: Final Output Provider → END ---")
    
        return Command(
            update={
                "messages": [
                    HumanMessage(content=agent_answer, name="final_output_provider")
                ]
            },
            goto=END, 
        )