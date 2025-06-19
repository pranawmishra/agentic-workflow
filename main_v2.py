from dotenv import load_dotenv
import uuid

load_dotenv()

import pprint
from src.graphs.agent_flow_v2 import AgentFlowV2
from src.utils.utils import save_graph_to_image

def main(app):
    print("(Type 'exit' or 'quit' or 'bye' to quit)")
    
    # Create a thread ID for this session
    thread_id = str(uuid.uuid4())
    print(f"Using conversation thread: {thread_id}")
    
    # Config for memory persistence
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("Enter your query: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye! Have a great day!")
            break

        inputs = {
            "messages": [
                ("user", user_input),
            ]
        }

        for event in app.stream(inputs, config=config):
            for key, value in event.items():
                if value is None:
                    continue
                last_message = value.get("messages", [])[-1] if "messages" in value else None
                if last_message and last_message.name == "final_output_provider" or last_message.name == "general_answer_provider":
                    pprint.pprint(f"Output from node '{key}':")
                    pprint.pprint(last_message, indent=2, width=80, depth=None)
                    print()

if __name__ == "__main__":

    app = AgentFlowV2()()
    save_graph_to_image(app, "src/images/graph.png", xray=True)
    # input_query = input("Enter your query: ")
    main(app)