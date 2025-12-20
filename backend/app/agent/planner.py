def plan(user_text: str, state):
    facts = state.facts or {}

    # naive parsing (demo-safe)
    if "वय" in user_text:
        age = int("".join(filter(str.isdigit, user_text)))
        return {"action": "store", "key": "age", "value": age}

    if "उत्पन्न" in user_text:
        income = int("".join(filter(str.isdigit, user_text)))
        return {"action": "store", "key": "income", "value": income}

    if "age" not in facts:
        return {"action": "ask", "prompt": "आपली वय किती आहे?"}

    if "income" not in facts:
        return {"action": "ask", "prompt": "आपले उत्पन्न किती आहे?"}

    return {
        "action": "recommend",
        "prompt": "आपण योग्य सरकारी योजनेसाठी पात्र आहात."
    }
