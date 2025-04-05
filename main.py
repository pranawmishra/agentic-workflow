from typing import Dict, List
import uuid
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from src.graphs.agent_flow import graph

def display_message(message):
    """Display a single message."""
    if message.type == "human":
        print(f"\n🧑 User: {message.content}")
    elif message.type == "ai":
        print(f"\n🤖 AI: {message.content}")
    else:
        print(f"\n🔄 System: {message.content}")

def main():
    """Run the LangGraph agent in a CLI interface with streaming and memory."""
    print("🌟 Welcome to the Weather & Document Assistant! 🌟")
    print("(Type 'exit' to quit)")
    
    # Create a thread ID for this session
    thread_id = str(uuid.uuid4())
    print(f"Using conversation thread: {thread_id}")
    
    # Config for memory persistence
    config = {"configurable": {"thread_id": thread_id}}
    
    # Main interaction loop
    while True:
        # Get user input
        user_input = input("\n🧑 You: ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\n🤖 AI: Goodbye! Have a great day!")
            break
        
        # Create human message
        human_message = {"role": "user", "content": user_input}
        
        # Stream the response with memory persistence
        print("\n🤖 AI: ", end="", flush=True)
        
        for step in graph.stream(
            {"messages": [human_message]},
            stream_mode="values",
            config=config,
        ):
            if "messages" in step and len(step["messages"]) > 1:
                latest_message = step["messages"][-1]
                # Only print AI message content, not tool calls
                if latest_message.type == "ai" and not getattr(latest_message, "tool_calls", None):
                    print(latest_message.content, end="", flush=True)
        
        print()  # Add newline after streaming completes

if __name__ == "__main__":
    main()
