from langgraph.graph import StateGraph, MessagesState, START
from langchain_cohere import ChatCohere
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from src.graphs.nodes import SupervisorNode, EnhancerNode, ResearcherNode, AnalystNode, ValidatorNode, FinalOutputProviderNode, GeneralAnswerProviderNode
from typing import Optional, List

class OverallState(MessagesState):
    supervisor_output: Optional[List[str]] = []
    supervisor_reason: Optional[List[str]] = []
    enhancer_output: Optional[List[str]] = []
    researcher_output: Optional[List[str]] = []
    analyst_output: Optional[List[str]] = []
    user_query: Optional[List[str]] = []
    final_output: Optional[List[str]] = []
    tool_calls_made: Optional[int] = []
    validator_output: Optional[List[str]] = []

class AgentFlowV2:
    def __init__(self):
        # self.llm = ChatCohere(
        #     model="command-a-03-2025",
        #     temperature=0.0,
        #     # cohere_api_key=os.getenv("COHERE_API_KEY")
        # )

        # self.llm = ChatGoogleGenerativeAI(
        #     model="gemini-2.5-flash",
        #     temperature=0,
        #     max_tokens=None,
        #     timeout=None,
        #     max_retries=2,
        #     # thinking_config={"thinking_budget": 1024},
        #     thinking_budget=1024,
        #     api_key=os.getenv("GEMINI_API_KEY")
        # )
        self.llm = ChatAnthropic(model="claude-3-5-haiku-latest")

        self.memory = MemorySaver()

    def __call__(self):

        graph = StateGraph(OverallState)

        graph.add_node("supervisor", SupervisorNode(self.llm)) 
        graph.add_node("enhancer", EnhancerNode(self.llm))  
        graph.add_node("researcher", ResearcherNode(self.llm)) 
        graph.add_node("analyst", AnalystNode(self.llm)) 
        graph.add_node("validator", ValidatorNode(self.llm))  
        graph.add_node("final_output_provider", FinalOutputProviderNode(self.llm))
        graph.add_node("general_answer_provider", GeneralAnswerProviderNode(self.llm))

        graph.add_edge(START, "supervisor")  
        app = graph.compile(checkpointer=self.memory)

        return app
