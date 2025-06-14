from langgraph.graph import StateGraph, MessagesState, START
from langchain_cohere import ChatCohere
from langchain_anthropic import ChatAnthropic
from src.graphs.nodes import SupervisorNode, EnhancerNode, ResearcherNode, CodeNode, ValidatorNode

class AgentFlowV2:
    def __init__(self):
        # self.llm = ChatCohere(
        #     model="command-a-03-2025",
        #     temperature=0.0,
        #     cohere_api_key=os.getenv("COHERE_API_KEY")
        # )
        self.llm = ChatAnthropic(model="claude-3-5-haiku-latest")

    def __call__(self):

        graph = StateGraph(MessagesState)

        graph.add_node("supervisor", SupervisorNode(self.llm)) 
        graph.add_node("enhancer", EnhancerNode(self.llm))  
        graph.add_node("researcher", ResearcherNode(self.llm)) 
        graph.add_node("coder", CodeNode(self.llm)) 
        graph.add_node("validator", ValidatorNode(self.llm))  

        graph.add_edge(START, "supervisor")  
        app = graph.compile()

        return app
