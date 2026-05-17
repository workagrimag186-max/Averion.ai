# Embedding Model Selection

## Chosen Model for MVP

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

This is our default embedding model for the MVP phase.

---

## What Are Embeddings?

**Simple explanation:** Embeddings convert text into numerical vectors (arrays of numbers).

Think of it like this:
- Text: `"The cat sat on the mat"`
- Embedding: `[0.23, -0.45, 0.67, ..., 0.12]` (384 numbers)

**Why do we need them?**

Computers can't directly understand text similarity. But they can compare numbers!

Embeddings capture the *meaning* of text as numbers, so we can:
- Find similar documents
- Search by semantic meaning (not just keywords)
- Power AI retrieval systems

Example:
- `"dog"` and `"puppy"` have similar embeddings (close meaning)
- `"dog"` and `"car"` have different embeddings (different meaning)

---

## Why This Model?

We chose `all-MiniLM-L6-v2` because it's perfect for MVPs:

### ✅ Fast
- Generates embeddings in milliseconds
- Won't slow down your application

### ✅ Lightweight
- Only ~80MB model size
- Low memory usage (~500MB RAM)
- Runs on regular laptops

### ✅ Good Enough Accuracy
- Produces 384-dimensional vectors
- Sufficient for most document search tasks
- Proven in production by many startups

### ✅ Works Locally
- No API calls needed
- No usage costs
- No internet dependency
- Complete privacy

### ✅ Widely Used
- Battle-tested by thousands of developers
- Excellent documentation
- Large community support

---

## Tradeoffs

### Pros ✅
- **Fast inference:** ~10ms per sentence
- **Low memory:** Runs on 4GB RAM machines
- **Free & open-source:** No licensing costs
- **Easy local setup:** One pip install
- **No API limits:** Unlimited usage

### Cons ⚠️
- **Lower accuracy:** Not as good as larger models
- **Limited complexity:** Struggles with very nuanced semantic tasks
- **English-focused:** Best for English text
- **Fixed dimensions:** 384 dimensions (can't be changed)

---

## Model Comparison

### vs. OpenAI Embeddings (`text-embedding-3-small`)
| Feature | all-MiniLM-L6-v2 | OpenAI |
|---------|------------------|--------|
| **Cost** | Free | ~$0.02 per 1M tokens |
| **Speed** | Very fast (local) | Slower (API call) |
| **Accuracy** | Good | Better |
| **Privacy** | Complete | Data sent to OpenAI |
| **Setup** | Simple | Requires API key |

**Verdict:** OpenAI is better quality, but our model is free and private.

### vs. Larger Sentence-Transformers (`all-mpnet-base-v2`)
| Feature | all-MiniLM-L6-v2 | all-mpnet-base-v2 |
|---------|------------------|-------------------|
| **Size** | 80MB | 420MB |
| **Speed** | Fast | Slower (3x) |
| **Accuracy** | Good | Better |
| **Dimensions** | 384 | 768 |

**Verdict:** Larger model is more accurate, but our model is faster and lighter.

---

## Local Setup

### Installation

```bash
pip install sentence-transformers
```

### Basic Usage

```python
from sentence_transformers import SentenceTransformer

# Load model (downloads automatically on first use)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Generate embedding for a single text
embedding = model.encode("Hello world")
print(embedding.shape)  # Output: (384,)

# Generate embeddings for multiple texts (batch processing)
texts = [
    "The quick brown fox",
    "jumps over the lazy dog",
    "Machine learning is awesome"
]
embeddings = model.encode(texts)
print(embeddings.shape)  # Output: (3, 384)
```

### Integration Example

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Embed document chunks
chunks = [
    "FastAPI is a modern web framework",
    "Python is great for AI applications",
    "Vector databases store embeddings"
]

# Generate embeddings
chunk_embeddings = model.encode(chunks)

# Embed user query
query = "What is FastAPI?"
query_embedding = model.encode(query)

# Find most similar chunk (cosine similarity)
from sklearn.metrics.pairwise import cosine_similarity
similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
most_similar_idx = np.argmax(similarities)

print(f"Most relevant chunk: {chunks[most_similar_idx]}")
# Output: "FastAPI is a modern web framework"
```

---

## When to Upgrade

Consider upgrading to a better model when:

1. **Accuracy matters more than speed**
   - Use `all-mpnet-base-v2` (still free, local)
   - Or OpenAI embeddings (paid, better quality)

2. **You have budget for APIs**
   - OpenAI `text-embedding-3-small` or `text-embedding-3-large`
   - Cohere embeddings

3. **You need multilingual support**
   - Use `paraphrase-multilingual-MiniLM-L12-v2`

4. **You have GPU resources**
   - Larger models become feasible
   - Speed is no longer a concern

---

## Summary

For our MVP, `sentence-transformers/all-MiniLM-L6-v2` is the **perfect choice**:
- Fast enough for real-time search
- Accurate enough for document retrieval
- Free and runs locally
- Easy to set up and use

We can always upgrade later if needed, but this model will serve us well for the initial launch.

---

## Resources

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [Model Card on Hugging Face](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) (Model benchmarks)