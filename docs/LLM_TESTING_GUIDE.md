# Testing Guide for Issue #21: LLM Provider Integration

This guide shows you how to verify that the LLM provider integration is working properly.

## Quick Test: Run the Manual Tests

The easiest way to verify everything works:

```bash
cd apps/api
python -m pytest tests/test_llm_manual.py -v -s
```

**Expected Output:**
- ✅ 4 tests should PASS
- You'll see mock responses being generated
- Complete RAG pipeline demonstration

---

## Method 1: Test the LLM Service Directly

### Test with Mock Provider (No API Key Needed)

```bash
cd apps/api
python -c "
from app.ai.llm_service import generate_answer
from app.ai.prompt_builder import build_rag_prompt

# Create a simple test
chunks = [{
    'document_id': 'test_doc',
    'chunk_index': 0,
    'chunk_id': 'test_doc_0',
    'text': 'Python is a high-level programming language.'
}]

prompt = build_rag_prompt('What is Python?', chunks)
answer = generate_answer(prompt)
print('Answer:', answer)
"
```

**Expected Output:**
```
Answer: Mock response: Based on the provided context, I can answer your question about 'What is Python?'. This is a simulated answer for testing purposes.
```

---

## Method 2: Test the Complete API Endpoint

### Step 1: Start the API Server

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 2: Test the /chat Endpoint

Open a new terminal and run:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is FastAPI?"}'
```

**Expected Response:**
```json
{
  "conversation_id": "some-uuid",
  "message_id": "some-uuid",
  "answer": "Mock response: Based on the provided context...",
  "citations": []
}
```

### Step 3: Test with Actual Documents

First, upload a document:

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@your-document.pdf"
```

Then ask a question about it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the document say about X?"}'
```

---

## Method 3: Test with OpenAI (Requires API Key)

### Step 1: Configure OpenAI

Edit `apps/api/.env`:

```bash
LLM_PROVIDER=openai
LLM_PROVIDER_API_KEY=sk-your-actual-openai-api-key-here
```

### Step 2: Run the OpenAI Test

```bash
cd apps/api
python -m pytest tests/test_llm_manual.py::test_llm_with_openai_provider -v -s
```

**Expected Output:**
- Real OpenAI API call
- Actual AI-generated response
- Test should PASS

### Step 3: Test via API

Start the server and make a request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain quantum computing in simple terms"}'
```

**Expected Response:**
- Real AI-generated answer from OpenAI
- Proper citations if documents are available

---

## Method 4: Interactive Testing with Swagger UI

### Step 1: Start the Server

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

### Step 2: Open Swagger UI

Navigate to: http://localhost:8000/docs

### Step 3: Test the /chat Endpoint

1. Find the `POST /chat` endpoint
2. Click "Try it out"
3. Enter a test question:
   ```json
   {
     "question": "What is machine learning?"
   }
   ```
4. Click "Execute"
5. Check the response

---

## Verification Checklist

Use this checklist to verify everything works:

### ✅ Basic Functionality
- [ ] Mock provider generates responses
- [ ] Prompt builder creates proper prompts
- [ ] LLM service handles empty context
- [ ] Error handling works (invalid provider, missing API key)

### ✅ API Integration
- [ ] Server starts without errors
- [ ] `/chat` endpoint is available
- [ ] POST requests return valid responses
- [ ] Response includes answer and citations

### ✅ RAG Pipeline
- [ ] Question → Embedding → Retrieval works
- [ ] Retrieved chunks are included in prompt
- [ ] LLM generates answer based on context
- [ ] Citations reference source documents

### ✅ OpenAI Integration (Optional)
- [ ] OpenAI provider works with valid API key
- [ ] Real AI responses are generated
- [ ] Error handling for API failures
- [ ] Rate limiting is respected

---

## Troubleshooting

### Issue: "Unsupported LLM provider: placeholder"

**Solution:** Update `.env` file:
```bash
LLM_PROVIDER=mock
```

### Issue: "OpenAI API key is not configured"

**Solution:** Either:
1. Use mock provider (default)
2. Add OpenAI API key to `.env`:
   ```bash
   LLM_PROVIDER=openai
   LLM_PROVIDER_API_KEY=sk-your-key-here
   ```

### Issue: Server won't start

**Solution:** Check for import errors:
```bash
cd apps/api
python -c "from app.main import app; print('OK')"
```

### Issue: No documents to retrieve

**Solution:** Upload documents first:
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample.pdf"
```

---

## Expected Test Results

When running `pytest tests/test_llm_manual.py -v -s`:

```
tests/test_llm_manual.py::test_llm_with_mock_provider PASSED
tests/test_llm_manual.py::test_llm_with_no_context PASSED
tests/test_llm_manual.py::test_llm_with_openai_provider PASSED (or SKIPPED)
tests/test_llm_manual.py::test_complete_rag_pipeline PASSED

============================== 4 passed in 0.20s ==============================
```

---

## Summary

The LLM integration is working if:
1. ✅ Manual tests pass (4/4)
2. ✅ Mock provider generates responses
3. ✅ API endpoint returns valid JSON
4. ✅ Complete RAG pipeline works end-to-end

For production use with real AI, configure OpenAI API key in `.env`.