def detect_contradictions(memory, new_facts):
    contradictions = []

    existing = memory.get("facts", {})

    for k, v in new_facts.items():
        if k in existing and existing[k] != v:
            contradictions.append(
                f"{k} changed from {existing[k]} to {v}"
            )

    return contradictions
