"""
Tests for cosine distance score filtering in RAG retrieval.

Validates that the filtering logic correctly handles cosine distance semantics
where lower scores indicate MORE similarity.
"""

import pytest

from app.ai.security import filter_chunks_by_score, validate_retrieval_score


class TestValidateRetrievalScore:
    """Test individual score validation against threshold."""
    
    def test_highly_similar_chunk_passes(self):
        """Highly similar chunks (low distance) should pass."""
        assert validate_retrieval_score(0.1, threshold=0.5) is True
        assert validate_retrieval_score(0.2, threshold=0.5) is True
    
    def test_moderately_similar_chunk_passes(self):
        """Moderately similar chunks should pass with appropriate threshold."""
        assert validate_retrieval_score(0.4, threshold=0.5) is True
        assert validate_retrieval_score(0.5, threshold=0.5) is True
    
    def test_dissimilar_chunk_fails(self):
        """Dissimilar chunks (high distance) should fail."""
        assert validate_retrieval_score(0.6, threshold=0.5) is False
        assert validate_retrieval_score(0.8, threshold=0.5) is False
        assert validate_retrieval_score(1.0, threshold=0.5) is False
    
    def test_edge_case_exact_threshold(self):
        """Score exactly at threshold should pass (<=)."""
        assert validate_retrieval_score(0.5, threshold=0.5) is True
        assert validate_retrieval_score(0.7, threshold=0.7) is True
    
    def test_strict_threshold(self):
        """Strict threshold (0.3) should only pass very similar chunks."""
        assert validate_retrieval_score(0.1, threshold=0.3) is True
        assert validate_retrieval_score(0.3, threshold=0.3) is True
        assert validate_retrieval_score(0.4, threshold=0.3) is False
    
    def test_permissive_threshold(self):
        """Permissive threshold (0.8) should pass loosely related chunks."""
        assert validate_retrieval_score(0.5, threshold=0.8) is True
        assert validate_retrieval_score(0.7, threshold=0.8) is True
        assert validate_retrieval_score(0.9, threshold=0.8) is False


class TestFilterChunksByScore:
    """Test chunk filtering with various score distributions."""
    
    def test_empty_list(self):
        """Empty input should return empty output."""
        result = filter_chunks_by_score([], threshold=0.5)
        assert result == []
    
    def test_all_chunks_pass(self):
        """All chunks below threshold should be kept."""
        chunks = [
            {"text": "chunk1", "score": 0.1},
            {"text": "chunk2", "score": 0.3},
            {"text": "chunk3", "score": 0.4},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 3
        assert result == chunks
    
    def test_all_chunks_fail(self):
        """All chunks above threshold should be filtered out."""
        chunks = [
            {"text": "chunk1", "score": 0.6},
            {"text": "chunk2", "score": 0.8},
            {"text": "chunk3", "score": 1.0},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert result == []
    
    def test_mixed_scores(self):
        """Should keep only chunks meeting threshold."""
        chunks = [
            {"text": "chunk1", "score": 0.2},  # KEEP
            {"text": "chunk2", "score": 0.4},  # KEEP
            {"text": "chunk3", "score": 0.6},  # FILTER
            {"text": "chunk4", "score": 0.8},  # FILTER
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 2
        assert result[0]["text"] == "chunk1"
        assert result[1]["text"] == "chunk2"
    
    def test_preserves_order(self):
        """Should preserve original order from vector search."""
        chunks = [
            {"text": "chunk1", "score": 0.3},
            {"text": "chunk2", "score": 0.1},
            {"text": "chunk3", "score": 0.4},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 3
        assert result[0]["text"] == "chunk1"
        assert result[1]["text"] == "chunk2"
        assert result[2]["text"] == "chunk3"
    
    def test_edge_case_at_threshold(self):
        """Chunks exactly at threshold should pass."""
        chunks = [
            {"text": "chunk1", "score": 0.5},
            {"text": "chunk2", "score": 0.50001},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 1
        assert result[0]["text"] == "chunk1"
    
    def test_missing_score_filtered(self):
        """Chunks without score should be filtered out."""
        chunks = [
            {"text": "chunk1", "score": 0.3},
            {"text": "chunk2"},  # No score
            {"text": "chunk3", "score": None},  # None score
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 1
        assert result[0]["text"] == "chunk1"
    
    def test_real_world_scenario(self):
        """Test with realistic scores from actual retrieval."""
        # These are the actual scores from the bug report
        chunks = [
            {
                "text": "FastAPI is a modern web framework",
                "document_id": "doc1",
                "score": 0.931528  # This was being filtered with threshold=0.7
            },
            {
                "text": "FastAPI supports async operations",
                "document_id": "doc1",
                "score": 0.931877  # This was being filtered with threshold=0.7
            }
        ]
        
        # With old threshold (0.7), these would be filtered out
        result_old = filter_chunks_by_score(chunks, threshold=0.7)
        assert len(result_old) == 0  # BUG: legitimate chunks filtered
        
        # With new threshold (0.5), these are correctly filtered
        # (they're not similar enough - 0.93 distance is quite far)
        result_new = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result_new) == 0  # CORRECT: these aren't similar
        
        # But with a more permissive threshold, they pass
        result_permissive = filter_chunks_by_score(chunks, threshold=1.0)
        assert len(result_permissive) == 2  # Both pass
    
    def test_highly_relevant_chunks(self):
        """Test that truly relevant chunks pass the filter."""
        chunks = [
            {"text": "chunk1", "score": 0.05},  # Nearly identical
            {"text": "chunk2", "score": 0.15},  # Highly similar
            {"text": "chunk3", "score": 0.35},  # Moderately similar
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 3
    
    def test_irrelevant_chunks(self):
        """Test that irrelevant chunks are filtered out."""
        chunks = [
            {"text": "chunk1", "score": 0.9},   # Barely related
            {"text": "chunk2", "score": 1.2},   # Not related
            {"text": "chunk3", "score": 1.8},   # Opposite meaning
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 0


class TestThresholdBehavior:
    """Test different threshold values and their effects."""
    
    def test_threshold_0_3_strict(self):
        """Threshold 0.3 should only pass very similar chunks."""
        chunks = [
            {"text": "chunk1", "score": 0.1},   # PASS
            {"text": "chunk2", "score": 0.25},  # PASS
            {"text": "chunk3", "score": 0.35},  # FAIL
            {"text": "chunk4", "score": 0.5},   # FAIL
        ]
        result = filter_chunks_by_score(chunks, threshold=0.3)
        assert len(result) == 2
    
    def test_threshold_0_5_moderate(self):
        """Threshold 0.5 should pass moderately similar chunks."""
        chunks = [
            {"text": "chunk1", "score": 0.2},   # PASS
            {"text": "chunk2", "score": 0.4},   # PASS
            {"text": "chunk3", "score": 0.6},   # FAIL
            {"text": "chunk4", "score": 0.8},   # FAIL
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 2
    
    def test_threshold_0_7_permissive(self):
        """Threshold 0.7 should pass loosely related chunks."""
        chunks = [
            {"text": "chunk1", "score": 0.3},   # PASS
            {"text": "chunk2", "score": 0.6},   # PASS
            {"text": "chunk3", "score": 0.8},   # FAIL
            {"text": "chunk4", "score": 1.0},   # FAIL
        ]
        result = filter_chunks_by_score(chunks, threshold=0.7)
        assert len(result) == 2
    
    def test_threshold_1_0_very_permissive(self):
        """Threshold 1.0 should pass even weakly related chunks."""
        chunks = [
            {"text": "chunk1", "score": 0.5},   # PASS
            {"text": "chunk2", "score": 0.8},   # PASS
            {"text": "chunk3", "score": 0.95},  # PASS
            {"text": "chunk4", "score": 1.1},   # FAIL
        ]
        result = filter_chunks_by_score(chunks, threshold=1.0)
        assert len(result) == 3


class TestRegressionPrevention:
    """Tests to prevent the specific bug that was reported."""
    
    def test_bug_scenario_with_old_threshold(self):
        """
        Reproduce the exact bug scenario:
        - Scores: 0.931528, 0.931877
        - Old threshold: 0.7
        - Result: Both filtered out (BUG)
        """
        chunks = [
            {"text": "chunk1", "score": 0.931528},
            {"text": "chunk2", "score": 0.931877},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.7)
        assert len(result) == 0  # This was the bug
    
    def test_bug_scenario_with_new_threshold(self):
        """
        With new threshold (0.5), these chunks are correctly filtered
        because 0.93 distance indicates they're not very similar.
        """
        chunks = [
            {"text": "chunk1", "score": 0.931528},
            {"text": "chunk2", "score": 0.931877},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 0  # Correctly filtered
    
    def test_legitimate_chunks_pass_new_threshold(self):
        """
        Truly relevant chunks (low distance) should pass the new threshold.
        """
        chunks = [
            {"text": "chunk1", "score": 0.15},  # Highly similar
            {"text": "chunk2", "score": 0.35},  # Moderately similar
            {"text": "chunk3", "score": 0.48},  # Still good
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 3  # All pass
    
    def test_no_context_scenario(self):
        """
        When no chunks meet threshold, should return empty list
        (triggering "no_context_available" response).
        """
        chunks = [
            {"text": "chunk1", "score": 0.8},
            {"text": "chunk2", "score": 0.9},
        ]
        result = filter_chunks_by_score(chunks, threshold=0.5)
        assert len(result) == 0  # Correct: no relevant context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
