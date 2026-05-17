"""
Retrieval Evaluation Script

This script loads the evaluation dataset and tests retrieval quality
by checking if expected documents are retrieved for each question.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.retrieval import retrieve_chunks


def load_eval_dataset():
    """Load the evaluation dataset from JSON file."""
    dataset_path = Path(__file__).parent / "retrieval_eval_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval():
    """
    Evaluate retrieval quality using the test dataset.
    
    For each question:
    - Retrieve top chunks
    - Check if expected document is in results
    - Print results for manual inspection
    """
    dataset = load_eval_dataset()
    
    print("=" * 80)
    print("RETRIEVAL EVALUATION")
    print("=" * 80)
    print()
    
    total_questions = len(dataset)
    matches = 0
    
    for i, entry in enumerate(dataset, 1):
        question = entry["question"]
        expected_doc = entry["expected_document"]
        expected_keywords = entry["expected_keywords"]
        
        print(f"[{i}/{total_questions}] Question: {question}")
        print(f"Expected Document: {expected_doc}")
        print(f"Expected Keywords: {', '.join(expected_keywords)}")
        print()
        
        try:
            # Retrieve chunks for the question
            results = retrieve_chunks(question, top_k=3)
            
            if not results:
                print("❌ No results retrieved")
                print()
                print("-" * 80)
                print()
                continue
            
            # Check top result
            top_result = results[0]
            print(f"Top Result (Score: {top_result.get('score', 'N/A')}):")
            print(f"Document ID: {top_result.get('document_id', 'N/A')}")
            print(f"Text: {top_result.get('text', '')[:200]}...")
            print()
            
            # Check if expected document matches
            retrieved_doc_id = top_result.get('document_id', '')
            if retrieved_doc_id == expected_doc:
                print("✅ Expected document found in top result")
                matches += 1
            else:
                # Check if it's in top 3
                found_in_top3 = any(
                    r.get('document_id') == expected_doc 
                    for r in results
                )
                if found_in_top3:
                    print("⚠️  Expected document found in top 3 (not top 1)")
                else:
                    print("❌ Expected document NOT found in top 3")
            
            print()
            
        except Exception as e:
            print(f"❌ Error during retrieval: {str(e)}")
            print()
        
        print("-" * 80)
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Questions: {total_questions}")
    print(f"Top-1 Matches: {matches}")
    print(f"Accuracy: {(matches / total_questions * 100):.1f}%")
    print()


if __name__ == "__main__":
    evaluate_retrieval()

# Made with Bob
