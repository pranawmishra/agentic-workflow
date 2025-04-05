import streamlit as st
import uuid
import os
import tempfile
import sys
from langchain_core.messages import HumanMessage, AIMessage
from src.graphs.agent_flow import graph

# Try to import document-related functions
try:
    from src.tools.document import get_qdrant_db, document_query
    DOCUMENT_TOOLS_AVAILABLE = True
except (ImportError, ValueError):
    DOCUMENT_TOOLS_AVAILABLE = False

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
        
    if "active_collection" not in st.session_state:
        st.session_state.active_collection = None
        
    # UI state variables
    if "show_all_collections" not in st.session_state:
        st.session_state.show_all_collections = False
        
    if "collections_refreshed" not in st.session_state:
        st.session_state.collections_refreshed = False
        
    if "show_preview" not in st.session_state:
        st.session_state.show_preview = False
        
    if "show_diagnostics" not in st.session_state:
        st.session_state.show_diagnostics = False

def upload_and_process_pdf():
    """Handle PDF upload and processing."""
    uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")
    
    if uploaded_file is not None:
        # Collection name input
        collection_name = st.text_input(
            "Collection name (optional)", 
            placeholder="Leave blank for auto-generated name"
        )
        collection_name = collection_name if collection_name else None
        
        # Process button
        if st.button("Process PDF"):
            with st.spinner("Processing PDF document..."):
                # Save uploaded file to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    pdf_path = tmp_file.name
                
                try:
                    # Create database instance
                    db = get_qdrant_db()
                    
                    # Create collection
                    with st.status("Creating vector database...") as status:
                        status.update(label="Loading document...")
                        
                        # First status update
                        status.update(label="Splitting document into chunks...")
                        
                        # Second status update
                        status.update(label="Generating embeddings...")
                        
                        # Create collection
                        result = db.create_collection(pdf_path, collection_name)
                        
                        # Final status
                        if "error" in result:
                            status.update(label=f"Error: {result['error']}", state="error")
                        else:
                            status.update(
                                label=f"Success! Created collection: {result['collection_name']}", 
                                state="complete"
                            )
                            st.session_state.active_collection = result["collection_name"]
                    
                    # Display result
                    if "error" not in result:
                        st.success(f"Document processed successfully! Collection: {result['collection_name']}")
                        st.session_state.messages.append(
                            AIMessage(content=f"I've processed your document and created a collection named '{result['collection_name']}'. You can now ask questions about it!")
                        )
                    else:
                        st.error(result["error"])
                
                finally:
                    # Clean up the temp file
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass

def display_collection_selector():
    """Display a dropdown to select an active collection with refresh option."""
    if DOCUMENT_TOOLS_AVAILABLE:
        st.subheader("Select Collection")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            try:
                db = get_qdrant_db()
                
                # Add a refresh button
                with col2:
                    if st.button("🔄", help="Refresh collections list"):
                        st.session_state.collections_refreshed = True
                        st.rerun()
                
                collections = db.get_collections()
                
                if collections:
                    # Create a more informative dropdown with collection count
                    selected_collection = st.selectbox(
                        f"Available collections ({len(collections)})",
                        options=collections,
                        index=0 if st.session_state.active_collection not in collections else collections.index(st.session_state.active_collection)
                    )
                    
                    if selected_collection != st.session_state.active_collection:
                        st.session_state.active_collection = selected_collection
                        st.success(f"Switched to collection: {selected_collection}")
                        
                    # Show active collection with better styling
                    if st.session_state.active_collection:
                        st.markdown(f"**Active collection:** `{st.session_state.active_collection}`")
                        
                        # Add a button to view collection details
                        if st.button("View Collection Details"):
                            # Query collection metadata (document count, etc.)
                            try:
                                # Use direct database query instead of document_query tool
                                result = db.query_collection("", st.session_state.active_collection)
                                if "error" not in result:
                                    doc_count = len(result.get("results", []))
                                    st.info(f"Collection '{st.session_state.active_collection}' contains {doc_count} documents/chunks.")
                                else:
                                    st.warning(f"Could not retrieve details: {result.get('error')}")
                            except Exception as e:
                                st.error(f"Error retrieving collection details: {str(e)}")
                else:
                    st.info("🔍 No document collections available. Upload a PDF to create one.")
                    
                    # Add a demo collection example
                    st.markdown("""
                    **How to use collections:**
                    1. Upload a PDF document in the 'Upload Document' section
                    2. Process the document to create a collection
                    3. Select the collection and ask questions about its content
                    """)
            except Exception as e:
                st.error(f"Error loading collections: {str(e)}")
                st.button("Try Again")

def display_all_collections():
    """Display all available collections in a formatted table."""
    if not DOCUMENT_TOOLS_AVAILABLE:
        return
        
    try:
        db = get_qdrant_db()
        collections = db.get_collections()
        
        if not collections:
            st.info("No collections available yet. Upload a document to create one.")
            return
            
        st.subheader(f"Available Collections ({len(collections)})")
        
        # Create columns for the table header
        cols = st.columns([3, 1, 1])
        cols[0].markdown("**Collection Name**")
        cols[1].markdown("**Status**")
        cols[2].markdown("**Action**")
        
        st.divider()
        
        # Display each collection
        for collection in collections:
            cols = st.columns([3, 1, 1])
            # Collection name
            cols[0].markdown(f"`{collection}`")
            
            # Status (active or not)
            if collection == st.session_state.active_collection:
                cols[1].markdown("✅ **Active**")
            else:
                cols[1].markdown("Inactive")
            
            # Action button
            if collection != st.session_state.active_collection:
                if cols[2].button("Select", key=f"select_{collection}"):
                    st.session_state.active_collection = collection
                    st.success(f"Switched to collection: {collection}")
                    st.rerun()
            else:
                cols[2].button("Selected", key=f"selected_{collection}", disabled=True)
                
        st.divider()
        
    except Exception as e:
        st.error(f"Error loading collections: {str(e)}")

def preview_collection_documents():
    """Display a preview of documents in the currently selected collection."""
    if not DOCUMENT_TOOLS_AVAILABLE or not st.session_state.active_collection:
        return
    
    try:
        # Get database instance
        db = get_qdrant_db()
        
        # Get a sample of documents from the collection using direct query
        result = db.query_collection("Show me a sample of this document", st.session_state.active_collection)
        
        if "error" in result:
            st.warning(f"Could not retrieve documents: {result.get('error')}")
            return
            
        documents = result.get("results", [])
        
        if not documents:
            st.info("No documents found in this collection.")
            return
            
        st.subheader(f"Preview of '{st.session_state.active_collection}'")
        
        # Show 3 document samples maximum
        for i, doc in enumerate(documents[:3]):
            with st.expander(f"Document sample {i+1}"):
                st.markdown(doc.get("page_content", "No content"))
                st.caption(f"Source: {doc.get('metadata', {}).get('source', 'Unknown')}, Page: {doc.get('metadata', {}).get('page', 'N/A')}")
                
        # If there are more than 3 documents, show a message
        if len(documents) > 3:
            st.caption(f"Showing 3 of {len(documents)} document chunks. Ask questions to search through all content.")
    
    except Exception as e:
        st.error(f"Error previewing documents: {str(e)}")

def diagnose_collection_issues():
    """Diagnose and potentially fix collection access issues."""
    if not DOCUMENT_TOOLS_AVAILABLE:
        return
    
    st.subheader("💻 Collection Diagnostics")
    
    try:
        db = get_qdrant_db()
        available_collections = db.get_collections()
        
        if not available_collections:
            st.warning("No collections are available in the database.")
            return
            
        st.write("### Checking available collections")
        st.success(f"Found {len(available_collections)} collections in Qdrant database.")
        
        # Display all collections
        for i, collection in enumerate(available_collections):
            st.write(f"{i+1}. `{collection}`")
        
        # Test collection access
        st.write("### Testing collection access")
        collection_to_test = st.selectbox(
            "Select a collection to test",
            options=available_collections
        )
        
        if st.button("Test Collection Access"):
            with st.spinner(f"Testing access to collection '{collection_to_test}'..."):
                # First, check if the collection exists in Qdrant
                try:
                    retriever = db.return_retriever(collection_to_test)
                    if retriever:
                        st.success(f"✅ Successfully accessed collection '{collection_to_test}'!")
                        
                        # Try a direct query to verify it's working using the database object
                        # instead of the document_query tool which expects run context
                        try:
                            result = db.query_collection("Test query", collection_to_test)
                            if "error" not in result:
                                st.success("✅ Successfully queried the collection.")
                                st.session_state.active_collection = collection_to_test
                            else:
                                st.error(f"❌ Error querying collection: {result.get('error')}")
                        except Exception as query_error:
                            st.error(f"❌ Query error: {str(query_error)}")
                    else:
                        st.error(f"❌ Failed to create retriever for collection '{collection_to_test}'.")
                except Exception as e:
                    st.error(f"❌ Exception: {str(e)}")
    
    except Exception as e:
        st.error(f"Error during diagnostics: {str(e)}")

def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="LangGraph Weather & Document Assistant", page_icon="🌦️", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("🌦️ Weather and Document Assistant")
    
    # Create sidebar for document operations
    with st.sidebar:
        st.header("Document Management")
        
        if DOCUMENT_TOOLS_AVAILABLE:
            # Collection selector - moved to top
            display_collection_selector()
            
            st.divider()
            
            # PDF Upload section
            st.subheader("Upload New Document")
            upload_and_process_pdf()
            
            # View all collections button
            if st.button("View All Collections"):
                st.session_state.show_all_collections = not st.session_state.get("show_all_collections", False)
                st.session_state.show_diagnostics = False
                st.session_state.show_preview = False
                
            # Preview documents in collection
            if st.session_state.active_collection and st.button("Preview Collection Content"):
                st.session_state.show_preview = not st.session_state.get("show_preview", False)
                st.session_state.show_all_collections = False
                st.session_state.show_diagnostics = False
                
            # Collection diagnostics button
            if st.button("⚠️ Diagnose Collection Issues"):
                st.session_state.show_diagnostics = not st.session_state.get("show_diagnostics", False)
                st.session_state.show_all_collections = False
                st.session_state.show_preview = False
                
        else:
            st.warning("Document tools are not available. Please check your environment variables for Qdrant and VoyageAI API keys.")
    
    # Main area for chat
    # Display active collection status in main area
    if DOCUMENT_TOOLS_AVAILABLE and st.session_state.active_collection:
        st.info(f"🔍 You're currently querying the '{st.session_state.active_collection}' collection. Ask any questions about this document.")
    
    # Show requested content based on state
    if DOCUMENT_TOOLS_AVAILABLE:
        if st.session_state.get("show_all_collections", False):
            display_all_collections()
        
        if st.session_state.get("show_preview", False) and st.session_state.active_collection:
            preview_collection_documents()
            
        if st.session_state.get("show_diagnostics", False):
            diagnose_collection_issues()
    
    st.markdown("""
    Ask me about:
    - **Weather**: Current weather for any location
    - **Documents**: Ask questions about uploaded PDFs
    """)
    
    # Display thread ID (for debugging, can be hidden in production)
    st.caption(f"Conversation thread: {st.session_state.thread_id}")
    
    # Display chat history
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)
    
    # Chat input
    if prompt := st.chat_input("Ask me about weather or your documents..."):
        # Add user message to display history
        user_message = HumanMessage(content=prompt)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            
        # Create config with thread_id for memory persistence
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        # If we have an active collection, include it in the prompt
        if DOCUMENT_TOOLS_AVAILABLE and st.session_state.active_collection:
            enhanced_prompt = f"{prompt} [Collection: {st.session_state.active_collection}]"
        else:
            enhanced_prompt = prompt
            
        # Run agent with user input
        with st.spinner("Thinking..."):
            # Create raw message for the graph
            human_message = {"role": "user", "content": enhanced_prompt}
            
            # Invoke the graph
            result = graph.invoke(
                {"messages": [human_message]},
                config=config
            )
            
            # Extract AI response (skip human message)
            if "messages" in result and len(result["messages"]) > 1:
                ai_message = result["messages"][-1]
                
                # Add to display messages
                st.session_state.messages.append(ai_message)
                
                # Display AI response
                with st.chat_message("assistant"):
                    st.write(ai_message.content)

if __name__ == "__main__":
    main() 