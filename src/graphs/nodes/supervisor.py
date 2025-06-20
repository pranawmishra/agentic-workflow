from pydantic import BaseModel, Field
from typing import Literal
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_cohere import ChatCohere

class Supervisor(BaseModel):
    next: Literal["enhancer", "researcher", "coder", "general_answer_provider"] = Field(
        description="Determines which specialist to activate next in the workflow sequence: "
                    "'enhancer' when user input requires clarification, expansion, or refinement, "
                    "'researcher' when additional facts, context, or data collection is necessary, "
                    "'coder' when implementation, computation, or technical problem-solving is required, "
                    "'general_answer_provider' when the task is not clear or the user's request is not possible to complete or the user query does not require any of the other agents."
    )
    reason: str = Field(
        description="Detailed justification for the routing decision, explaining the rationale behind selecting the particular specialist and how this advances the task toward completion."
    )

class SupervisorNode:
    def __init__(self, llm: ChatCohere):
        self.llm = llm

    def __call__(self, state: MessagesState) -> Command[Literal["enhancer", "researcher", "coder", "general_answer_provider"]]:

        system_prompt = ('''
                    
            You are a workflow supervisor managing a team of three specialized agents: Prompt Enhancer, Researcher, and Coder. Your role is to orchestrate the workflow by selecting the most appropriate next agent based on the current state and needs of the task. Provide a clear, concise rationale for each decision to ensure transparency in your decision-making process.

            **Team Members**:
            1. **Prompt Enhancer**: Use when the user's request has sufficient context but needs refinement or restructuring for better clarity. The core intent should be identifiable.
            2. **Researcher**: Specializes in information gathering, fact-finding, and collecting relevant data needed to address the user's request.
            3. **Coder**: Focuses on technical implementation, calculations, data analysis, algorithm development, and coding solutions when requirements are clear and specific.
            4. **General Answer Provider**: Use when the user's request is too vague, incomplete, or impossible to complete. This agent can ask for clarification or provide general guidance.

            **Your Responsibilities**:
            1. Analyze each user request and agent response for completeness, accuracy, and relevance.
            2. Route the task to the most appropriate agent at each decision point.
            3. Maintain workflow momentum by avoiding redundant agent assignments.
            4. Continue the process until the user's request is fully and satisfactorily resolved.

            Your objective is to create an efficient workflow that leverages each agent's strengths while minimizing unnecessary steps, ultimately delivering complete and accurate solutions to user requests.
                    
        ''')
        
        messages = [
            {"role": "system", "content": system_prompt},  
        ] + state["messages"] 

        response = self.llm.with_structured_output(Supervisor).invoke(messages)

        goto = response.next
        reason = response.reason

        print(f"--- Workflow Transition: Supervisor → {goto.upper()} ---")
        
        return Command(
            update={
                "messages": [
                    HumanMessage(content=reason, name="supervisor")
                ]
            },
            goto=goto,  
        )