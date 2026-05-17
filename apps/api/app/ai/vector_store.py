import chromadb

# Initialize ChromaDB with persistent storage
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection("documents")


def store_embeddings(chunks: list[dict]) -> None:
    """
    Store embeddings in ChromaDB.
    
    Args:
        chunks: List of chunk dictionaries with document_id, chunk_index,
                page_number, text, and embedding fields
    """
    # Batch insert - collect all data first
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        # Skip chunks without embeddings
        if "embedding" not in chunk:
            continue
        
        try:
            # Create unique ID for the chunk
            chunk_id = f"{chunk['document_id']}_{chunk['chunk_index']}"
            
            # Append to batch lists
            ids.append(chunk_id)
            embeddings.append(chunk["embedding"])
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk["page_number"]
            })
        except Exception as e:
            # Skip failed chunks silently
            continue
    
    # Batch insert all chunks at once
    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )


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
        
        # Safety checks
        if not results:
            return []
        
        documents_list = results.get("documents", [[]])
        metadatas_list = results.get("metadatas", [[]])
        distances_list = results.get("distances", [[]])
        
        if not documents_list or not metadatas_list or not distances_list:
            return []
        
        if not documents_list[0]:
            return []
        
        documents = documents_list[0]
        metadatas = metadatas_list[0]
        distances = distances_list[0]
        
        # Build output list
        output = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append({
                "text": doc,
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index"),
                "page_number": meta.get("page_number"),
                "score": dist
            })
        
        return output
        
    except Exception as e:
        # Return empty list on error
        return []

# Made with Bob
