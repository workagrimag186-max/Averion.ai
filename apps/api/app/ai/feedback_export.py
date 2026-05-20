"""
Feedback Review Dataset Export

This script exports user feedback data from the database into structured datasets
for evaluation and improvement of the AI system.

Usage:
    python -m app.ai.feedback_export
    python -m app.ai.feedback_export --format csv --output feedback.csv
    python -m app.ai.feedback_export --all-feedback

Example output (JSONL):
    {"question": "What is X?", "answer": "X is...", "citations": [...], "rating": "down", "correction": "Better answer"}
    {"question": "How to Y?", "answer": "To Y...", "citations": [], "rating": "down", "correction": null}
"""

import argparse
import csv
import json
from pathlib import Path

import psycopg

from app.core.config import settings
from app.db.connection import is_database_configured
from app.db.documents import DatabaseNotConfiguredError
from app.db.schema import FeedbackRating


def export_feedback_dataset(
    format: str = "jsonl",
    output_path: str = "feedback_export.jsonl",
    negative_only: bool = True
) -> None:
    """
    Export feedback dataset from database.
    
    Args:
        format: Output format - "jsonl" or "csv"
        output_path: Path to output file
        negative_only: If True, export only negative feedback (default)
    
    Raises:
        DatabaseNotConfiguredError: If DATABASE_URL is not configured
    """
    if not is_database_configured():
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    if settings.database_url is None:
        raise DatabaseNotConfiguredError("DATABASE_URL is not configured.")

    with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            query = """
                select
                    user_msg.content as question,
                    asst_msg.content as answer,
                    asst_msg.citations as citations,
                    f.rating,
                    f.correction_text as correction
                from feedback f
                join messages asst_msg on f.message_id = asst_msg.id
                join lateral (
                    select content
                    from messages
                    where conversation_id = asst_msg.conversation_id
                        and role = 'user'
                        and created_at < asst_msg.created_at
                    order by created_at desc
                    limit 1
                ) user_msg on true
            """
            
            if negative_only:
                query += " where f.rating = %s"
                cursor.execute(query + " order by f.created_at desc", (FeedbackRating.DOWN.value,))
            else:
                cursor.execute(query + " order by f.created_at desc")

            rows = cursor.fetchall()

    records = []
    for row in rows:
        citations = row[2] if row[2] else []
        if isinstance(citations, str):
            try:
                citations = json.loads(citations)
            except json.JSONDecodeError:
                citations = []
        
        record = {
            "question": row[0],
            "answer": row[1],
            "citations": citations,
            "rating": row[3],
            "correction": row[4]
        }
        records.append(record)

    output_file = Path(output_path)
    
    if format == "jsonl":
        with output_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    elif format == "csv":
        with output_file.open("w", encoding="utf-8", newline="") as f:
            fieldnames = ["question", "answer", "rating", "correction", "citations"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                csv_record = {
                    "question": record["question"],
                    "answer": record["answer"],
                    "rating": record["rating"],
                    "correction": record["correction"] or "",
                    "citations": json.dumps(record["citations"], ensure_ascii=False)
                }
                writer.writerow(csv_record)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'jsonl' or 'csv'.")
    
    print(f"Exported {len(records)} feedback records to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Export feedback dataset for evaluation and improvement"
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv"],
        default="jsonl",
        help="Output format (default: jsonl)"
    )
    parser.add_argument(
        "--output",
        default="feedback_export.jsonl",
        help="Output file path (default: feedback_export.jsonl)"
    )
    parser.add_argument(
        "--all-feedback",
        action="store_true",
        help="Export all feedback, not just negative (default: negative only)"
    )
    
    args = parser.parse_args()
    
    export_feedback_dataset(
        format=args.format,
        output_path=args.output,
        negative_only=not args.all_feedback
    )


if __name__ == "__main__":
    main()

# Made with Bob
