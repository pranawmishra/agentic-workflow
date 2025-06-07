import os
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
# Get Tavily API key from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

@tool
def tavily_search(query: str) -> dict:
    """
    Perform a Web search using Tavily API.
    
    Args:
        query (str): The search query.
        
    Returns:
        dict: Search results from Tavily.
    """
    print("Using tool tavily_search")
    # return tavily_tool.run(query)
    tavily_tool = TavilySearch(
        max_results=10,
        topic="general",
        include_answer=True,
        # include_raw_content=False,
        # include_images=False,
        # include_image_descriptions=False,
        # search_depth="basic",
        # time_range="day",
        # include_domains=None,
        # exclude_domains=None
    )
    # msg = tavily_tool.invoke({"query": query})
    # return msg
    msg = tavily_tool.run(query)
    # print(len(msg["results"]), "results found")
    contents = [result["content"] for result in msg["results"]]
    return contents

if __name__ == "__main__":
    # Example usage
    query = "List all the california child abuse laws"
    results = tavily_search.invoke(query)
    # Print the results
    print(results)

