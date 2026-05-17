import chromadb
from chromadb.config import Settings


# Initialize ChromaDB client with persistent storage
client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

# Get or create collection for documents
collection = client.get_or_create_collection(name="documents")


def store_embeddings(chunks: list[dict]):
    """
    Store document chunks with embeddings in ChromaDB.
    
    Args:
        chunks: List of chunk dictionaries containing:
            - document_id: str
            - chunk_index: int
            - page_number: int
            - text: str
            - embedding: list[float]
    """
    if not chunks:
        return
    
    ids = []
    embeddings = []
    metadatas = []
    documents = []
    
    for chunk in chunks:
        # Skip chunks without embeddings
        if "embedding" not in chunk or not chunk["embedding"]:
            continue
        
        # Create unique ID
        chunk_id = f"{chunk['document_id']}_{chunk['chunk_index']}"
        ids.append(chunk_id)
        
        # Extract embedding
        embeddings.append(chunk["embedding"])
        
        # Create metadata
        metadata = {
            "document_id": chunk["document_id"],
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk["page_number"]
        }
        metadatas.append(metadata)
        
        # Extract text
        documents.append(chunk["text"])
    
    # Add to collection if we have valid chunks
    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )


def search_similar(query_embedding: list[float], top_k: int = 3):
    """
    Search for similar chunks using query embedding.
    
    Args:
        query_embedding: Query embedding vector
        top_k: Number of top results to return
        
    Returns:
        List of dictionaries containing:
            - text: str
            - metadata: dict
            - score: float (distance)
    """
    try:
        # Check if collection is empty
        if collection.count() == 0:
            return []
        
        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        
        if results and results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                result = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": results["distances"][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
        
    except Exception as e:
        print(f"Error during similarity search: {e}")
        return []

# Made with Bob
