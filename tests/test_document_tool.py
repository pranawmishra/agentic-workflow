import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.tools.document import document_query, list_collections, create_document_collection

# Sample document content for testing
SAMPLE_DOCUMENT_TEXT = """
This is a sample document for testing.
It contains information about Qdrant vector database.
Qdrant is a vector similarity search engine.
"""

# Sample document response data
SAMPLE_DOCUMENT_RESULTS = [
    {
        "page_content": "This is a sample document for testing.",
        "metadata": {"source": "test_doc.pdf", "page": 1}
    },
    {
        "page_content": "It contains information about Qdrant vector database.",
        "metadata": {"source": "test_doc.pdf", "page": 1}
    }
]

# Sample document collection response
SAMPLE_COLLECTION_RESPONSE = {
    "status": "success",
    "collection": "test_collection",
    "results": SAMPLE_DOCUMENT_RESULTS
}

class TestDocumentTool:
    """Test suite for the document tools."""
    
    def test_document_tools_exist(self):
        """Test that the document tools have the correct attributes from the decorator."""
        assert hasattr(document_query, "name")
        assert document_query.name == "document_query"
        assert "query" in document_query.args
        
        assert hasattr(list_collections, "name")
        assert list_collections.name == "list_collections"
        
        assert hasattr(create_document_collection, "name")
        assert create_document_collection.name == "create_document_collection"
        assert "file_path" in create_document_collection.args
    
    @patch('src.tools.document.QdrantDatabase.query_collection')
    def test_document_query_successful(self, mock_query_collection):
        """Test the document_query tool with a successful query."""
        # Configure the mock to return a successful response
        mock_query_collection.return_value = SAMPLE_COLLECTION_RESPONSE
        
        # Run the tool - modified to use input parameter
        result = document_query.invoke(input={"query": "test query", "collection_name": "test_collection"})
        
        # Assertions
        assert "status" in result
        assert result["status"] == "success"
        assert result["collection"] == "test_collection"
        assert len(result["results"]) == 2
        assert result["results"][0]["page_content"] == "This is a sample document for testing."
        
        # Verify the query method was called with the correct parameters
        mock_query_collection.assert_called_once_with("test query", "test_collection")
    
    @patch('src.tools.document.QdrantDatabase.query_collection')
    def test_document_query_error(self, mock_query_collection):
        """Test the document_query tool when an error occurs."""
        # Configure the mock to return an error
        mock_query_collection.return_value = {"error": "Collection not found"}
        
        # Run the tool - modified to use input parameter
        result = document_query.invoke(input={"query": "test query", "collection_name": "nonexistent_collection"})
        
        # Assertions
        assert "error" in result
        assert result["error"] == "Collection not found"
        
        # Verify the query method was called
        mock_query_collection.assert_called_once()
    
    @patch('src.tools.document.QdrantDatabase.get_collections')
    def test_list_collections(self, mock_get_collections):
        """Test the list_collections tool."""
        # Configure the mock to return a list of collections
        mock_get_collections.return_value = ["collection1", "collection2", "collection3"]
        
        # Run the tool - modified to use input parameter (empty dict for no args)
        result = list_collections.invoke(input={})
        
        # Assertions
        assert "collections" in result
        assert len(result["collections"]) == 3
        assert "collection1" in result["collections"]
        assert "collection2" in result["collections"]
        assert "collection3" in result["collections"]
        
        # Verify the get_collections method was called
        mock_get_collections.assert_called_once()
    
    @patch('src.tools.document.QdrantDatabase.create_collection')
    def test_create_document_collection(self, mock_create_collection):
        """Test the create_document_collection tool."""
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_file:
            tmp_file.write(b"PDF content")
            tmp_file.flush()
            
            # Configure the mock to return a successful response
            mock_create_collection.return_value = {
                "collection_name": "test_collection",
                "document_count": 10
            }
            
            # Run the tool - modified to use input parameter
            result = create_document_collection.invoke(
                input={
                    "file_path": tmp_file.name,
                    "collection_name": "test_collection"
                }
            )
            
            # Assertions
            assert "collection_name" in result
            assert result["collection_name"] == "test_collection"
            assert result["document_count"] == 10
            
            # Verify the create_collection method was called with the correct parameters
            mock_create_collection.assert_called_once_with(tmp_file.name, "test_collection")
    
    @patch('src.tools.document.QdrantDatabase.create_collection')
    def test_create_document_collection_error(self, mock_create_collection):
        """Test the create_document_collection tool when an error occurs."""
        # Configure the mock to return an error
        mock_create_collection.return_value = {"error": "Invalid PDF file"}
        
        # Run the tool - modified to use input parameter
        result = create_document_collection.invoke(
            input={
                "file_path": "nonexistent.pdf",
                "collection_name": "test_collection"
            }
        )
        
        # Assertions
        assert "error" in result
        assert result["error"] == "Invalid PDF file"
        
        # Verify the create_collection method was called
        mock_create_collection.assert_called_once()