"""
Tests for the ingestion pipeline.

Tests the full pipeline: extraction → cleaning → chunking
"""

import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path for standalone execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.ingestion_pipeline import run_ingestion_pipeline
from app.ai.cleaning import clean_text
from app.ai.chunking import chunk_text

# Base directory points to apps/api/
BASE_DIR = Path(__file__).resolve().parent.parent


def get_test_file_path(filename):
    """Get the full path to a test file"""
    return str(BASE_DIR / filename)


def test_full_pipeline_txt():
    """Test full pipeline with TXT file"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="txt",
        document_id="test-doc-txt",
        page_number=1
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify chunk structure
    for i, chunk in enumerate(chunks):
        assert "document_id" in chunk, f"Chunk {i} missing document_id"
        assert "chunk_index" in chunk, f"Chunk {i} missing chunk_index"
        assert "page_number" in chunk, f"Chunk {i} missing page_number"
        assert "text" in chunk, f"Chunk {i} missing text"
        assert chunk["text"] and chunk["text"].strip(), f"Chunk {i} has empty text"
        assert chunk["document_id"] == "test-doc-txt", f"Chunk {i} has wrong document_id"
        assert chunk["page_number"] == 1, f"Chunk {i} has wrong page_number"


def test_full_pipeline_pdf():
    """Test full pipeline with PDF file"""
    file_path = get_test_file_path("sample.pdf")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="pdf",
        document_id="test-doc-pdf",
        page_number=2
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify chunk structure
    for i, chunk in enumerate(chunks):
        assert "document_id" in chunk, f"Chunk {i} missing document_id"
        assert "chunk_index" in chunk, f"Chunk {i} missing chunk_index"
        assert "page_number" in chunk, f"Chunk {i} missing page_number"
        assert "text" in chunk, f"Chunk {i} missing text"
        assert chunk["text"] and chunk["text"].strip(), f"Chunk {i} has empty text"
        assert chunk["document_id"] == "test-doc-pdf", f"Chunk {i} has wrong document_id"
        assert chunk["page_number"] == 2, f"Chunk {i} has wrong page_number"


def test_full_pipeline_docx():
    """Test full pipeline with DOCX file"""
    file_path = get_test_file_path("sample.docx")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="docx",
        document_id="test-doc-docx",
        page_number=3
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify chunk structure
    for i, chunk in enumerate(chunks):
        assert "document_id" in chunk, f"Chunk {i} missing document_id"
        assert "chunk_index" in chunk, f"Chunk {i} missing chunk_index"
        assert "page_number" in chunk, f"Chunk {i} missing page_number"
        assert "text" in chunk, f"Chunk {i} missing text"
        assert chunk["text"] and chunk["text"].strip(), f"Chunk {i} has empty text"
        assert chunk["document_id"] == "test-doc-docx", f"Chunk {i} has wrong document_id"
        assert chunk["page_number"] == 3, f"Chunk {i} has wrong page_number"


def test_empty_input():
    """Test pipeline with empty inputs"""
    # Test clean_text with empty string
    result = clean_text("")
    assert result == "", f"clean_text('') should return empty string, got: {repr(result)}"
    
    # Test chunk_text with empty string
    chunks = chunk_text("", "test-doc", 1)
    assert chunks == [], f"chunk_text('') should return empty list, got: {chunks}"
    
    # Test pipeline with invalid file
    chunks = run_ingestion_pipeline(
        file_path="nonexistent_file.txt",
        file_type="txt",
        document_id="test-doc",
        page_number=1
    )
    assert chunks == [], f"Invalid file should return empty list, got: {chunks}"


def test_metadata_preservation():
    """Test that metadata is correctly preserved through pipeline"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    document_id = "metadata-test-doc"
    page_number = 42
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="txt",
        document_id=document_id,
        page_number=page_number
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify chunk_index increments correctly
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i, f"Chunk {i} has wrong chunk_index: {chunk['chunk_index']}"
    
    # Verify document_id is preserved
    for i, chunk in enumerate(chunks):
        assert chunk["document_id"] == document_id, f"Chunk {i} has wrong document_id: {chunk['document_id']}"
    
    # Verify page_number is preserved
    for i, chunk in enumerate(chunks):
        assert chunk["page_number"] == page_number, f"Chunk {i} has wrong page_number: {chunk['page_number']}"


def test_no_empty_chunks():
    """Test that no empty chunks are produced"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="txt",
        document_id="test-doc",
        page_number=1
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify no empty chunks
    for i, chunk in enumerate(chunks):
        assert chunk.get("text") and chunk["text"].strip(), f"Chunk {i} has empty text"


def test_unsupported_file_type():
    """Test pipeline with unsupported file type"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    # Test with unsupported file type
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="xyz",  # Unsupported type
        document_id="test-doc",
        page_number=1
    )
    
    assert chunks == [], "Unsupported file type should return empty list"


def test_chunk_index_sequence():
    """Test that chunk indices are sequential starting from 0"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="txt",
        document_id="test-doc",
        page_number=1
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i, f"Expected chunk_index {i}, got {chunk['chunk_index']}"


def test_page_number_optional():
    """Test that page_number can be None"""
    file_path = get_test_file_path("sample.txt")
    
    assert Path(file_path).exists(), f"File not found: {file_path}"
    
    chunks = run_ingestion_pipeline(
        file_path=file_path,
        file_type="txt",
        document_id="test-doc",
        page_number=None
    )
    
    assert chunks, "No chunks returned"
    assert len(chunks) > 0, "Expected at least one chunk"
    
    # Verify page_number is None in all chunks
    for i, chunk in enumerate(chunks):
        assert chunk["page_number"] is None, f"Chunk {i} should have None page_number"


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("INGESTION PIPELINE TESTS")
    print("=" * 60)
    print()
    
    tests = [
        ("Full Pipeline - TXT", test_full_pipeline_txt),
        ("Full Pipeline - PDF", test_full_pipeline_pdf),
        ("Full Pipeline - DOCX", test_full_pipeline_docx),
        ("Empty Input Handling", test_empty_input),
        ("Metadata Preservation", test_metadata_preservation),
        ("No Empty Chunks", test_no_empty_chunks),
        ("Unsupported File Type", test_unsupported_file_type),
        ("Chunk Index Sequence", test_chunk_index_sequence),
        ("Page Number Optional", test_page_number_optional),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            test_func()
            results.append((test_name, True))
            print(f"PASS: {test_name}")
        except AssertionError as e:
            print(f"FAIL: {test_name} - ASSERTION FAILED - {e}")
            results.append((test_name, False))
        except Exception as e:
            print(f"FAIL: {test_name} - EXCEPTION - {e}")
            results.append((test_name, False))
        print()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

# Made with Bob