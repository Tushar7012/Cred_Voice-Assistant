def evaluate_response(plan, result):
    if result is None:
        return False

    if not isinstance(result, str):
        return False

    if len(result.strip()) < 3:
        return False

    return True
