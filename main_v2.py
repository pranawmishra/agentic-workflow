from dotenv import load_dotenv

load_dotenv()

import pprint
from src.graphs.agent_flow_v2 import AgentFlowV2
from src.utils.utils import save_graph_to_image

def main(app, user_input: str):    

    inputs = {
        "messages": [
            ("user", user_input),
        ]
    }

    for event in app.stream(inputs):
        for key, value in event.items():
            if value is None:
                continue
            last_message = value.get("messages", [])[-1] if "messages" in value else None
            if last_message:
                pprint.pprint(f"Output from node '{key}':")
                pprint.pprint(last_message, indent=2, width=80, depth=None)
                print()

if __name__ == "__main__":

    app = AgentFlowV2()()
    save_graph_to_image(app, "src/images/graph.png", xray=True)
    input_query = input("Enter your query: ")
    main(app, input_query)