from app.tools.scheme_retriever import retrieve_scheme
from app.tools.eligibility_engine import check_eligibility

def execute_tools(plan, user_text):
    """
    FINAL Executor
    - Trusts planner
    - Never blocks valid answers
    - Never forces fallback loops
    """

    # 🔹 If planner already returned text, just speak it
    if isinstance(plan, str):
        return plan.strip()

    if not isinstance(plan, dict):
        return None

    tool = plan.get("tool", "direct_answer")

    # 🔹 Scheme retrieval
    if tool == "scheme_retriever":
        result = retrieve_scheme(user_text)
        return result.strip() if isinstance(result, str) else None

    # 🔹 Eligibility checking
    if tool == "eligibility_checker":
        result = check_eligibility(user_text)
        return result.strip() if isinstance(result, str) else None

    # 🔹 Direct answer (GK, history, general questions)
    reason = plan.get("reason")
    if isinstance(reason, str) and len(reason.strip()) > 2:
        return reason.strip()

    # 🔹 Absolute last fallback (should almost never trigger)
    return "मुझे इस प्रश्न का उत्तर अभी उपलब्ध नहीं है।"
