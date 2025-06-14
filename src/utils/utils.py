from langgraph.graph import StateGraph

def save_graph_to_image(app: StateGraph, filename: str = "src/images/graph.png", xray: bool = True):
    """
    Save the graph to an image file.

    Args:
        app: The LangGraph application.
        filename: The name of the file to save the image to.
    """
    # display(Image(app.get_graph(xray=xray).draw_mermaid_png()))
    graph_png = app.get_graph(xray=xray).draw_mermaid_png()

    with open(filename, "wb") as f:
        f.write(graph_png)


