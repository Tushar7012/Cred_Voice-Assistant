from app.tools.scheme_retriever import retrieve_scheme
from app.tools.eligibility_engine import check_eligibility

def execute_tools(plan, user_text):
    """
    Executor with safe fallback
    """

    # If planner returned plain text (most common case)
    if isinstance(plan, str):
        return plan

    tool = plan.get("tool")

    if tool == "scheme_retriever":
        return retrieve_scheme(user_text)

    if tool == "eligibility_checker":
        return check_eligibility(user_text)

    if tool == "direct_answer":
        return plan.get("reason")

    # FINAL fallback
    return plan.get("reason", "कृपया थोड़ा और विवरण दें।")

