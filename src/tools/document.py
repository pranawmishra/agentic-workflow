import os
import shutil
import tempfile
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_voyageai import VoyageAIEmbeddings
from langchain_cohere import CohereEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required environment variables
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# os.environ['VOYAGEAI_API_KEY'] = VOYAGE_API_KEY
# os.environ['QDRANT_API_KEY'] = QDRANT_API_KEY

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Qdrant URL and API key must be set in environment variables")

if not COHERE_API_KEY:
    raise ValueError("Cohere API key not found in environment variables")

# Global variables to store the database and active collection
qdrant_db = None
active_collection = None


def get_qdrant_db():
    """Get or create the QdrantDatabase instance."""
    global qdrant_db
    if qdrant_db is None:
        qdrant_db = QdrantDatabase()
    return qdrant_db

class QdrantDatabase:
    """
    A class to manage the creation, retrieval, and querying of collections in a Qdrant vector database.
    """
    def __init__(self):
        """
        Initializes the QdrantDatabase object with required configurations and embeddings.
        """
        self.used_documents_folder = os.path.join(os.getcwd(), 'src/used_documents')
        os.makedirs(self.used_documents_folder, exist_ok=True)
        
        self.url = QDRANT_URL
        self.qdrant_api_key = QDRANT_API_KEY
        # self.embeddings = VoyageAIEmbeddings(
        #     model='voyage-3-large',
        #     output_dimension=256, 
        #     truncation=True
        # )
        self.embeddings = CohereEmbeddings(model="embed-multilingual-v3.0",
                                           cohere_api_key=COHERE_API_KEY) 
        self.qdrant_client = QdrantClient(
            url=self.url,
            api_key=self.qdrant_api_key,
            prefer_grpc=True
        )

    def create_collection(self, file_path: str, collection_name: str = None):
        """
        Creates a Qdrant collection by loading documents from a file.

        Parameters:
        file_path (str): Path to the PDF file
        collection_name (str, optional): The name of the collection to create.

        Returns:
        tuple: (collection_name, retriever) - The name of the created collection and a retriever object
        """
        # If no collection name provided, create one based on filename
        if not collection_name:
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            collection_name = f"{base_name}_{uuid.uuid4().hex[:8]}"
        
        # Load the PDF
        loader = PyPDFLoader(file_path)
        documents = []
        try:
            documents.extend(loader.load())
        except Exception as e:
            return {"error": f"Error loading PDF: {str(e)}"}

        # Create the collection
        try:
            QdrantVectorStore.from_documents(
                documents,
                self.embeddings,
                url=self.url,
                api_key=self.qdrant_api_key,
                collection_name=collection_name
            )
            
            # Copy the file to used_documents folder
            dest_path = os.path.join(self.used_documents_folder, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            
            # Create retriever
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=collection_name,
                embedding=self.embeddings
            )
            retriever = vector_store.as_retriever()
            
            # Set as active collection
            global active_collection
            active_collection = collection_name
            
            return {
                "status": "success", 
                "collection_name": collection_name,
                "message": f"Collection {collection_name} created successfully with {len(documents)} documents."
            }
        except Exception as e:
            return {"error": f"Failed to create collection: {str(e)}"}

    def get_collections(self) -> list:
        """
        Retrieves the list of existing collections in the Qdrant database.

        Returns:
        list: A list of collection names.
        """
        collections = self.qdrant_client.get_collections()
        existing_indexes = [collection.name for collection in collections.collections]
        return existing_indexes

    def return_retriever(self, collection_name: str):
        """
        Creates a retriever object from existing collection in the Qdrant database.

        Parameters:
        collection_name (str): The name of the collection to create retriever.

        Returns:
        retriever: A retriever object for querying the specified collection.
        If the collection does not exist, returns None.
        """
        try:
            # Check if collection exists
            if collection_name not in self.get_collections():
                print(f"Collection '{collection_name}' not found in available collections.")
                return None
                
            # Get the collection
            if self.qdrant_client.get_collection(collection_name):
                print(f"Successfully found collection '{collection_name}' in Qdrant.")
                vector_store = QdrantVectorStore(
                    client=self.qdrant_client,
                    collection_name=collection_name,
                    embedding=self.embeddings
                )
                retriever = vector_store.as_retriever()
                return retriever
        except Exception as e:
            print(f"Error creating retriever for collection '{collection_name}': {str(e)}")
            return None
    
    def query_collection(self, query: str, collection_name: str = None) -> Dict[str, Any]:
        """
        Query a collection for relevant documents.
        
        Parameters:
        query (str): The query string
        collection_name (str, optional): The collection to query. If None, uses active collection.
        
        Returns:
        Dictionary with results or error information
        """
        global active_collection
        
        # If no collection specified, use the active one
        if not collection_name:
            collection_name = active_collection
        
        if not collection_name:
            return {"error": "No collection specified and no active collection."}
        
        # Check if collection exists in available collections
        available_collections = self.get_collections()
        if collection_name not in available_collections:
            return {
                "error": f"Collection '{collection_name}' not found.",
                "available_collections": available_collections,
                "suggestion": "Please select one of the available collections."
            }
        
        # Get the retriever
        retriever = self.return_retriever(collection_name)
        if not retriever:
            return {
                "error": f"Failed to create retriever for collection '{collection_name}'.",
                "suggestion": "The collection exists but could not be accessed. This might be due to missing embeddings or database connection issues."
            }
        
        # Query the collection
        try:
            docs = retriever.invoke(query)
            if not docs or len(docs) == 0:
                return {
                    "status": "success",
                    "collection": collection_name,
                    "message": "No relevant documents found for your query.",
                    "results": []
                }
            
            return {
                "status": "success",
                "collection": collection_name,
                "results": [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    } for doc in docs
                ]
            }
        except Exception as e:
            return {"error": f"Error querying collection: {str(e)}"}

@tool
def document_query(query: str, collection_name: str = None) -> Dict[str, Any]:
    """Tool that queries a document collection for relevant information based on the query"""
    print("Using tool document_query")
    db = get_qdrant_db()
    return db.query_collection(query, collection_name)

@tool
def list_collections() -> Dict[str, Any]:
    """Tool that lists all available document collections"""
    print("Using tool list_collections")
    db = get_qdrant_db()
    collections = db.get_collections()
    return {"status": "success", "collections": collections}

@tool
def create_document_collection(file_path: str, collection_name: str = None) -> Dict[str, Any]:
    """Tool that creates a new document collection from a PDF file"""
    print("Using tool create_document_collection")
    db = get_qdrant_db()
    return db.create_collection(file_path, collection_name) 