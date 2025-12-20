from app.agent.llama_planner import llama_plan
from app.agent.executor import execute_tools
from app.agent.evaluator import evaluate_response
from app.memory.memory_store import (
    get_session_memory,
    update_fact,
    append_history,
    add_contradiction
)
from app.utils.contradiction import detect_contradictions


def run_agent(user_text: str, language: str, session_id: str):
    """
    Stable agent loop:
    Planner → (Optional tools) → Memory
    """

    memory = get_session_memory(session_id)

    plan = llama_plan(user_text, language, memory)

    if isinstance(plan, str) and len(plan.strip()) > 20:
        append_history(session_id, "user", user_text)
        append_history(session_id, "assistant", plan)
        return plan

    result = execute_tools(plan, user_text)

    if isinstance(result, str) and len(result.strip()) > 20:
        append_history(session_id, "assistant", result)
        return result

    ok = evaluate_response(plan, result)

    if not ok:
        clarification = "कृपया अपनी उम्र, आय और राज्य की जानकारी दें।"
        append_history(session_id, "assistant", clarification)
        return clarification

    if isinstance(plan, dict):
        new_facts = plan.get("facts_to_store", {})

        contradictions = detect_contradictions(memory, new_facts)
        for c in contradictions:
            add_contradiction(session_id, c)

        for k, v in new_facts.items():
            update_fact(session_id, k, v)

    final_safe = "आप किस सरकारी योजना के बारे में जानकारी चाहते हैं?"
    append_history(session_id, "assistant", final_safe)
    return final_safe
