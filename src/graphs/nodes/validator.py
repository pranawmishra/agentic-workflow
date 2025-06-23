from typing import Literal
from langgraph.graph import END, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere
from pydantic import BaseModel, Field

# System prompt providing clear instructions to the validator agent
system_prompt = '''
    Your task is to ensure reasonable quality. 
    Specifically, you must:
    - Review the user's question (the first message in the workflow).
    - Review the answer (the last message in the workflow).
    - If the answer addresses the core intent of the question, even if not perfectly, signal to end the workflow with 'FINISH'.
    - Only route back to the supervisor if the answer is completely off-topic, harmful, or fundamentally misunderstands the question.
    
    - Accept answers that are "good enough" rather than perfect
    - Prioritize workflow completion over perfect responses
    - Give benefit of doubt to borderline answers
    
    Routing Guidelines:
    1. 'supervisor' Agent: ONLY for responses that are completely incorrect or off-topic.
    2. Respond with 'FINISH' in all other cases to end the workflow.
'''

class Validator(BaseModel):
    next: Literal["supervisor", "FINISH"] = Field(
        description="Specifies the next worker in the pipeline: 'supervisor' to continue or 'FINISH' to terminate."
    )
    reason: str = Field(
        description="The reason for the decision."
    )

class ValidatorNode:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: MessagesState) -> Command[Literal["supervisor", "final_output_provider"]]:

        user_question = state["messages"][0].content
        agent_answer = state["messages"][-1].content

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
            {"role": "user", "content": agent_answer},
        ]

        response = self.llm.with_structured_output(Validator).invoke(messages)

        goto = response.next
        reason = response.reason

        if goto == "FINISH":
            goto = "final_output_provider"
            print(f"--- Workflow Transition: Validator → Final Output Provider ---")
        else:
            print(f"--- Workflow Transition: Validator → Supervisor ---")
    

        return Command(
            update={
                "messages": [
                    HumanMessage(content=reason, name="validator")
                ]
            },
            goto=goto, 
        )