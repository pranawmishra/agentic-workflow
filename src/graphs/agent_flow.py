from typing import Annotated, List, Dict, Any, Optional
import os
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from src.tools import tools as available_tools

load_dotenv()
# Load environment variables from .env file
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
langsmith_tracing = os.getenv("LANGSMITH_TRACING")
# Set environment variables for LangSmith tracing and API key
os.environ["LANGSMITH_TRACING"]= langsmith_tracing
os.environ["LANGSMITH_API_KEY"]= langsmith_api_key

class WeatherDocumentAgent:
    """
    A class-based implementation of the Weather and Document Agent.
    Uses LangGraph for orchestration and LangChain tools for functionality.
    """
    
    def __init__(self, model_name="claude-3-7-sonnet-latest", use_memory=True):
        """
        Initialize the agent with the specified LLM model.
        
        Args:
            model_name: The name of the LLM model to use
            use_memory: Whether to use memory persistence
        """
        # Initialize the LLM
        self.llm = ChatAnthropic(model=model_name)
        
        # Initialize the graph
        self.graph_builder = StateGraph(MessagesState)
        
        # Create the tool node
        self.tool_node = ToolNode(available_tools)
        
        # Initialize memory saver if requested
        self.memory = MemorySaver() if use_memory else None
        
        # Build the graph
        self._build_graph()
        
        # Compile the graph
        self.graph = self.graph_builder.compile(checkpointer=self.memory)
    
    def query_or_respond(self, state: MessagesState) -> Dict[str, List[Any]]:
        """
        Generate tool call for retrieval or respond directly.
        
        Args:
            state: The current message state
            
        Returns:
            Updated state with new messages
        """
        llm_with_tools = self.llm.bind_tools(available_tools)
        response = llm_with_tools.invoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}
    
    def generate(self, state: MessagesState) -> Dict[str, List[Any]]:
        """
        Generate answer based on tool results.
        
        Args:
            state: The current message state
            
        Returns:
            Updated state with new messages
        """
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]

        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = self.llm.invoke(prompt)
        return {"messages": [response]}
    
    def _build_graph(self):
        """Build the LangGraph flow."""
        # Add nodes to the graph
        self.graph_builder.add_node("query_or_respond", self.query_or_respond)
        self.graph_builder.add_node("tools", self.tool_node)
        self.graph_builder.add_node("generate", self.generate)
        
        # Set the entry point
        self.graph_builder.set_entry_point("query_or_respond")
        
        # Add conditional edges
        self.graph_builder.add_conditional_edges(
            "query_or_respond",
            tools_condition,
            {END: END, "tools": "tools"},
        )
        
        # Add remaining edges
        self.graph_builder.add_edge("tools", "generate")
        self.graph_builder.add_edge("generate", END)
    
    def stream(self, messages, thread_id=None):
        """
        Stream responses from the agent.
        
        Args:
            messages: The messages to process
            thread_id: Optional thread ID for memory persistence
            
        Returns:
            A stream of responses
        """
        config = {}
        if thread_id and self.memory:
            config = {"configurable": {"thread_id": thread_id}}
        
        return self.graph.stream({"messages": messages}, config=config, stream_mode="values")


# Create an instance of the agent
agent = WeatherDocumentAgent()
# Export the compiled graph
graph = agent.graph