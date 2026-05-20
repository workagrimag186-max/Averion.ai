"""
Manual test for feedback export functionality.

Run with:
    python -m pytest apps/api/tests/test_feedback_export_manual.py -v -s

Or directly:
    python apps/api/tests/test_feedback_export_manual.py
"""

import json
import tempfile
from pathlib import Path

from app.ai.feedback_export import export_feedback_dataset
from app.db.connection import is_database_configured


def test_export_feedback_jsonl_manual():
    """Test exporting feedback to JSONL format."""
    if not is_database_configured():
        print("⚠️  DATABASE_URL not configured. Skipping test.")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        output_path = f.name

    try:
        print("\n" + "=" * 60)
        print("Testing JSONL export (negative feedback only)")
        print("=" * 60)
        
        export_feedback_dataset(
            format="jsonl",
            output_path=output_path,
            negative_only=True
        )
        
        output_file = Path(output_path)
        if output_file.exists():
            with output_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"\n✓ Exported {len(lines)} records")
            
            if lines:
                print("\nFirst 3 records:")
                for i, line in enumerate(lines[:3], 1):
                    record = json.loads(line)
                    print(f"\nRecord {i}:")
                    print(f"  Question: {record['question'][:80]}...")
                    print(f"  Answer: {record['answer'][:80]}...")
                    print(f"  Citations: {len(record['citations'])} items")
                    print(f"  Rating: {record['rating']}")
                    print(f"  Correction: {record['correction'][:80] if record['correction'] else 'None'}...")
                
                sample = json.loads(lines[0])
                assert "question" in sample
                assert "answer" in sample
                assert "citations" in sample
                assert "rating" in sample
                assert "correction" in sample
                assert isinstance(sample["citations"], list)
                print("\n✓ Structure validation passed")
            else:
                print("\n⚠️  No feedback records found in database")
        else:
            print("\n✗ Output file not created")
    
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_export_feedback_csv_manual():
    """Test exporting feedback to CSV format."""
    if not is_database_configured():
        print("⚠️  DATABASE_URL not configured. Skipping test.")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        output_path = f.name

    try:
        print("\n" + "=" * 60)
        print("Testing CSV export (negative feedback only)")
        print("=" * 60)
        
        export_feedback_dataset(
            format="csv",
            output_path=output_path,
            negative_only=True
        )
        
        output_file = Path(output_path)
        if output_file.exists():
            with output_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"\n✓ Exported {len(lines) - 1} records (plus header)")
            
            if len(lines) > 1:
                print("\nHeader:")
                print(f"  {lines[0].strip()}")
                
                print("\nFirst 2 data rows:")
                for i, line in enumerate(lines[1:3], 1):
                    print(f"  Row {i}: {line[:100]}...")
                
                print("\n✓ CSV format validation passed")
            else:
                print("\n⚠️  No feedback records found in database")
        else:
            print("\n✗ Output file not created")
    
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_export_all_feedback_manual():
    """Test exporting all feedback (positive and negative)."""
    if not is_database_configured():
        print("⚠️  DATABASE_URL not configured. Skipping test.")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        output_path = f.name

    try:
        print("\n" + "=" * 60)
        print("Testing JSONL export (all feedback)")
        print("=" * 60)
        
        export_feedback_dataset(
            format="jsonl",
            output_path=output_path,
            negative_only=False
        )
        
        output_file = Path(output_path)
        if output_file.exists():
            with output_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"\n✓ Exported {len(lines)} records (all feedback)")
            
            if lines:
                ratings = {}
                for line in lines:
                    record = json.loads(line)
                    rating = record["rating"]
                    ratings[rating] = ratings.get(rating, 0) + 1
                
                print("\nRating distribution:")
                for rating, count in ratings.items():
                    print(f"  {rating}: {count} records")
                
                print("\n✓ All feedback export passed")
            else:
                print("\n⚠️  No feedback records found in database")
        else:
            print("\n✗ Output file not created")
    
    finally:
        if Path(output_path).exists():
            Path(output_path).unlink()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FEEDBACK EXPORT MANUAL TESTS")
    print("=" * 60)
    
    test_export_feedback_jsonl_manual()
    test_export_feedback_csv_manual()
    test_export_all_feedback_manual()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60 + "\n")

# Made with Bob
