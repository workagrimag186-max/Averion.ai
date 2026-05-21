import chromadb
from typing import Any

from app.core.config import settings

# Initialize ChromaDB with persistent storage
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection("documents")


def build_chunk_id(document_id: str, chunk_index: int | str) -> str:
    return f"{document_id}:{chunk_index}"


def reset_collection() -> None:
    """
    Clear and recreate the documents collection.

    Use this only in tests or manual reset scripts. Normal document ingestion
    should upsert new chunks without deleting existing vectors.
    """
    global collection

    try:
        client.delete_collection("documents")
    except Exception:
        pass

    collection = client.get_or_create_collection("documents")


def store_embeddings(chunks: list[dict], clear_existing: bool = False) -> None:
    """
    Store embeddings in ChromaDB.
    
    Args:
        chunks: List of chunk dictionaries with document_id, chunk_index,
                page_number, text, and embedding fields
        clear_existing: When True, reset the collection before storing.
            This is intended for tests only.
    """
    if clear_existing:
        reset_collection()
    
    # Batch insert - collect all data first
    ids = []
    embeddings = []
    documents = []
    metadatas: list[dict[str, Any]] = []
    
    for chunk in chunks:
        # Skip chunks without embeddings
        if "embedding" not in chunk:
            continue
        
        try:
            document_id = str(chunk["document_id"])
            organization_id = str(
                chunk.get("organization_id") or settings.default_organization_id
            )
            chunk_index = chunk["chunk_index"]
            chunk_id = str(chunk.get("chunk_id") or build_chunk_id(document_id, chunk_index))
            page_number = chunk.get("page_number")
            
            # Append to batch lists
            ids.append(chunk_id)
            embeddings.append(chunk["embedding"])
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": document_id,
                "organization_id": organization_id,
                "chunk_index": int(chunk_index),
                "chunk_id": chunk_id,
                "page_number": page_number if page_number is not None else -1
            })
        except Exception:
            # Skip failed chunks silently
            continue
    
    # Batch insert all chunks at once
    if ids:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )


def search_similar(
    query_embedding: list[float],
    top_k: int = 3,
    organization_id: str | None = None
) -> list[dict]:
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
        where_filter = None
        if organization_id:
            where_filter = {"organization_id": organization_id}

        query_args: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter is not None:
            query_args["where"] = where_filter

        results = collection.query(**query_args)
        
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
            page_number = meta.get("page_number")

            output.append({
                "text": doc,
                "document_id": meta.get("document_id"),
                "organization_id": meta.get("organization_id"),
                "chunk_index": meta.get("chunk_index"),
                "chunk_id": meta.get("chunk_id"),
                "page_number": None if page_number == -1 else page_number,
                "score": dist
            })
        
        return output
        
    except Exception:
        # Return empty list on error
        return []

# Made with Bob
