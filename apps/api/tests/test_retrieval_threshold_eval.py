from app.core.config import settings


def test_default_retrieval_threshold_matches_labeled_score_eval() -> None:
    """
    Cosine distance scores are lower when chunks are more relevant.

    This tiny eval set documents why the default threshold is 0.8: it keeps
    the relevant/adjacent examples while rejecting weak and unrelated matches.
    """
    labeled_scores = [
        ("exact_policy_answer", 0.18, True),
        ("same_topic_paragraph", 0.56, True),
        ("adjacent_policy_context", 0.79, True),
        ("weak_tangent", 0.93, False),
        ("unrelated_company_bio", 1.21, False),
        ("opposite_topic", 1.58, False),
    ]

    predictions = [
        (label, score <= settings.retrieval_min_score)
        for label, score, _expected_relevant in labeled_scores
    ]
    expected = [
        (label, expected_relevant)
        for label, _score, expected_relevant in labeled_scores
    ]

    assert settings.retrieval_min_score == 0.8
    assert predictions == expected
