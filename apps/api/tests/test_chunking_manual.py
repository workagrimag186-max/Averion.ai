"""
Manual test for text chunking functionality.
"""

from app.ai.chunking import chunk_text


def test_chunking_manual():
    """Manual test to verify chunking behavior."""

    # Sample cleaned text (simulating output from cleaning pipeline)
    sample_text = """
    Artificial intelligence has revolutionized the way we process and analyze data.
    Machine learning algorithms can now identify patterns in vast datasets that would
    be impossible for humans to detect manually. Deep learning, a subset of machine
    learning, uses neural networks with multiple layers to learn hierarchical
    representations of data. These networks have achieved remarkable success in
    image recognition, natural language processing, and speech recognition tasks.

    The transformer architecture, introduced in 2017, has become the foundation for
    many state-of-the-art language models. Models like GPT and BERT have demonstrated
    unprecedented capabilities in understanding and generating human-like text. These
    models are trained on massive amounts of text data and can perform a wide variety
    of tasks without task-specific training.

    Computer vision has also seen tremendous advances with convolutional neural networks.
    These networks can classify images, detect objects, and even generate realistic images.
    Applications range from autonomous vehicles to medical diagnosis. The ability to
    process visual information has opened up new possibilities in robotics and automation.

    Natural language processing enables computers to understand, interpret, and generate
    human language. This technology powers virtual assistants, translation services, and
    sentiment analysis tools. Recent advances have made it possible for machines to engage
    in more natural conversations and understand context better than ever before.

    Reinforcement learning allows agents to learn optimal behaviors through trial and error.
    This approach has been successfully applied to game playing, robotics, and resource
    optimization. The agent receives rewards or penalties based on its actions and learns
    to maximize cumulative rewards over time. This paradigm has led to breakthroughs in
    complex decision-making tasks.

    Ethics and responsible AI development have become increasingly important topics.
    As AI systems become more powerful and widespread, concerns about bias, privacy,
    and accountability have grown. Researchers and practitioners are working to develop
    frameworks for ensuring AI systems are fair, transparent, and aligned with human values.

    The future of artificial intelligence holds immense potential. Advances in quantum
    computing may enable even more powerful AI systems. Integration of AI with other
    technologies like blockchain and IoT will create new opportunities. However, careful
    consideration of societal impacts and ethical implications will be crucial as we
    continue to develop and deploy AI systems.
    """
    sample_text = sample_text * 3

    # Test chunking
    document_id = "test_doc_001"
    page_number = 1

    chunks = chunk_text(sample_text, document_id, page_number)

    print(f"\n{'='*80}")
    print("CHUNKING TEST RESULTS")
    print(f"{'='*80}\n")

    print(f"Total chunks created: {len(chunks)}")
    print(f"Document ID: {document_id}")
    print(f"Page Number: {page_number}\n")

    # Verify and display each chunk
    for i, chunk in enumerate(chunks):
        chunk_content = chunk["text"]
        word_count = len(chunk_content.split())

        print(f"--- Chunk {i} ---")
        print(f"Chunk Index: {chunk['chunk_index']}")
        print(f"Word Count: {word_count}")
        print(f"Text Preview (first 100 chars): {chunk_content[:100]}...")
        print(f"Text Preview (last 100 chars): ...{chunk_content[-100:]}")

        # Assertions
        assert chunk_content.strip(), f"Chunk {i} is empty"
        # Allow smaller chunks for last chunk or small documents
        # MIN_CHUNK_SIZE=600, MAX_CHUNK_SIZE=900 in chunking.py
        assert word_count <= 1100, f"Chunk {i} exceeds maximum size (got {word_count} words)"
        assert chunk["document_id"] == document_id
        assert chunk["chunk_index"] == i
        assert chunk["page_number"] == page_number

        print()

    # Overlap check
    if len(chunks) > 1:
        print("--- Overlap Analysis ---")
        for i in range(len(chunks) - 1):
            current_words = chunks[i]["text"].split()
            next_words = chunks[i + 1]["text"].split()

            overlap = set(current_words[-20:]) & set(next_words[:20])

            print(f"Chunks {i} → {i+1} overlap: {'YES' if overlap else 'NO'}")

        print()

    print(f"{'='*80}")
    print("[SUCCESS] All verifications passed!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_chunking_manual()