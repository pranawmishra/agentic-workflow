from src.tools.weather import weather_tool
try:
    from src.tools.document import document_query, list_collections, create_document_collection
    # Successfully imported document tools
    tools = [weather_tool, document_query, list_collections, create_document_collection]
except (ImportError, ValueError) as e:
    # Document tools not available (e.g., missing Qdrant or VoyageAI credentials)
    print(f"Document tools not available: {str(e)}")
    tools = [weather_tool]

__all__ = ["weather_tool", "tools"]
# Add these only if they're available
try:
    from src.tools.document import document_query, list_collections, create_document_collection
    __all__.extend(["document_query", "list_collections", "create_document_collection"])
except (ImportError, ValueError):
    pass 