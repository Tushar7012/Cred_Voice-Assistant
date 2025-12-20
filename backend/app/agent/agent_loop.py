from app.agent.grok_planner import grok_plan
from app.agent.executor import execute_tools
from app.agent.evaluator import evaluate_response
from app.memory.memory_store import (
    get_session_memory,
    update_fact,
    append_history,
    add_contradiction
)
from app.utils.contradiction import detect_contradictions
from app.utils.memory_recall import build_memory_recall_text


def run_agent(user_text: str, language: str, session_id: str):
    """
    Full agent loop:
    Plan → Execute → Evaluate → Memory Update → Spoken Memory Recall
    """

    memory = get_session_memory(session_id)

    plan = grok_plan(user_text, language, memory)

    result = execute_tools(plan, user_text)

    ok = evaluate_response(plan, result)
    if not ok:
        return plan.get("reason")

    new_facts = plan.get("facts_to_store", {})

    contradictions = detect_contradictions(memory, new_facts)
    for c in contradictions:
        add_contradiction(session_id, c)

    for k, v in new_facts.items():
        update_fact(session_id, k, v)

    append_history(session_id, "user", user_text)
    append_history(session_id, "assistant", result)

    recall_text = build_memory_recall_text(memory, language)

    final_response = f"{recall_text}{result}"

    return final_response
