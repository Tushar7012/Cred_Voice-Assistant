def evaluate_response(plan, result):
    """
    Smarter evaluator:
    - Accepts any meaningful text
    - Rejects only empty / None
    """

    if result is None:
        return False

    if not isinstance(result, str):
        return False

    # Reject only truly useless responses
    bad_phrases = [
        "मुझे जानकारी नहीं",
        "माफ़ कीजिए",
        "कृपया थोड़ी और जानकारी",
    ]

    for phrase in bad_phrases:
        if phrase in result and len(result.strip()) < 40:
            return False

    return True
