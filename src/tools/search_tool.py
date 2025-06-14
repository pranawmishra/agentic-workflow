from langchain_tavily import TavilySearch
from langchain_core.tools import tool

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
        # api_key=settings.tavily_api_key,
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
    contents = [result["content"] for result in msg["results"]]
    return contents

if __name__ == "__main__":
    # Example usage
    query = "List all the california child abuse laws"
    results = tavily_search.invoke(query)
    # Print the results
    print(results)

