import chromadb

# Initialize ChromaDB with persistent storage
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="documents")


def store_embeddings(chunks: list[dict]) -> None:
    """
    Store embeddings in ChromaDB.
    
    Args:
        chunks: List of chunk dictionaries with document_id, chunk_index,
                page_number, text, and embedding fields
    """
    for chunk in chunks:
        # Skip chunks without embeddings
        if "embedding" not in chunk:
            continue
        
        try:
            # Create unique ID for the chunk
            chunk_id = f"{chunk['document_id']}_{chunk['chunk_index']}"
            
            # Add to collection
            collection.add(
                ids=[chunk_id],
                embeddings=[chunk["embedding"]],
                documents=[chunk["text"]],
                metadatas=[{
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk["page_number"]
                }]
            )
        except Exception as e:
            # Skip failed chunks silently
            continue


def search_similar(query_embedding: list[float], top_k: int = 3) -> list[dict]:
    """
    Search for similar chunks using query embedding.
    
    Args:
        query_embedding: Query vector
        top_k: Number of results to return
        
    Returns:
        List of similar chunks with text, metadata, and scores
    """
    try:
        # Check if collection is empty
        if collection.count() == 0:
            return []
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        
        # ChromaDB returns results in lists
        if results and results.get("documents") and len(results["documents"]) > 0:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            for i in range(len(documents)):
                formatted_results.append({
                    "text": documents[i],
                    "document_id": metadatas[i]["document_id"],
                    "chunk_index": metadatas[i]["chunk_index"],
                    "page_number": metadatas[i]["page_number"],
                    "score": distances[i]
                })
        
        return formatted_results
        
    except Exception as e:
        # Return empty list on error
        return []

# Made with Bob
