"""
Diagnostic script to check actual similarity scores from the vector database.
This will help us determine the optimal threshold.
"""
import sys
sys.path.insert(0, '.')

from app.ai.embeddings import embed_text
from app.ai.vector_store import search_similar
from app.core.config import settings

# Test query
test_query = "What is data request process?"

# Use the actual organization ID from your documents
actual_org_id = "afe598c8-20e7-4edf-ae0e-86810dcdb044"

print(f"\n{'='*60}")
print(f"Testing query: '{test_query}'")
print(f"Current threshold: {settings.retrieval_min_score}")
print(f"Using Organization ID: {actual_org_id}")
print(f"Default Organization ID: {settings.default_organization_id}")
print(f"{'='*60}\n")

# Generate embedding
print("Generating query embedding...")
query_embedding = embed_text(test_query)
print(f"Embedding dimension: {len(query_embedding)}")

# Search without filtering
print("\nSearching for similar chunks (top 10)...")
results = search_similar(
    query_embedding,
    top_k=10,
    organization_id=actual_org_id
)

print(f"\nFound {len(results)} chunks:")
print(f"{'='*60}")

for i, result in enumerate(results, 1):
    print(f"\nChunk {i}:")
    print(f"  Score: {result['score']:.4f}")
    print(f"  Document ID: {result['document_id']}")
    print(f"  Chunk Index: {result['chunk_index']}")
    print(f"  Text preview: {result['text'][:100]}...")
    print(f"  Passes threshold ({settings.retrieval_min_score})? {result['score'] <= settings.retrieval_min_score}")

if results:
    scores = [r['score'] for r in results]
    print(f"\n{'='*60}")
    print(f"Score Statistics:")
    print(f"  Minimum: {min(scores):.4f}")
    print(f"  Maximum: {max(scores):.4f}")
    print(f"  Average: {sum(scores)/len(scores):.4f}")
    print(f"\nRecommended threshold: {max(scores[0:3]):.4f} (to get top 3 results)")
else:
    print("\nNo results found! Check if documents are properly indexed.")

# Made with Bob
