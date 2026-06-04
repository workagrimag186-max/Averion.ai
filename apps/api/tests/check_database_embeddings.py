"""
Check what's actually in the document_embeddings table.
"""
import sys
sys.path.insert(0, '.')

import psycopg
from app.core.config import settings

print(f"\n{'='*60}")
print("Checking document_embeddings table")
print(f"{'='*60}\n")

if not settings.database_url:
    print("ERROR: DATABASE_URL not configured!")
    sys.exit(1)

try:
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            # Check total embeddings
            cur.execute("SELECT COUNT(*) FROM document_embeddings")
            total = cur.fetchone()[0]
            print(f"Total embeddings in database: {total}")
            
            # Check by organization
            cur.execute("""
                SELECT organization_id, COUNT(*) 
                FROM document_embeddings 
                GROUP BY organization_id
            """)
            print("\nEmbeddings by organization:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]} embeddings")
            
            # Check specific organization
            target_org = "afe598c8-20e7-4edf-ae0e-86810dcdb044"
            cur.execute("""
                SELECT COUNT(*) 
                FROM document_embeddings 
                WHERE organization_id = %s::uuid
            """, (target_org,))
            count = cur.fetchone()[0]
            print(f"\nEmbeddings for target org ({target_org}): {count}")
            
            # Sample some embeddings
            if count > 0:
                cur.execute("""
                    SELECT chunk_id, document_id, chunk_index, 
                           LEFT(text, 50) as text_preview,
                           array_length(embedding, 1) as embedding_dim
                    FROM document_embeddings 
                    WHERE organization_id = %s::uuid
                    LIMIT 5
                """, (target_org,))
                print("\nSample embeddings:")
                for row in cur.fetchall():
                    print(f"  Chunk: {row[0]}")
                    print(f"    Document: {row[1]}")
                    print(f"    Index: {row[2]}")
                    print(f"    Text: {row[3]}...")
                    print(f"    Embedding dim: {row[4]}")
                    print()
            
            # Check documents table
            cur.execute("""
                SELECT id, filename, status, 
                       (SELECT COUNT(*) FROM document_chunks WHERE document_id = documents.id) as chunk_count
                FROM documents 
                WHERE organization_id = %s::uuid
            """, (target_org,))
            print("\nDocuments in database:")
            for row in cur.fetchall():
                print(f"  {row[1]}: status={row[2]}, chunks={row[3]}")
                
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob
