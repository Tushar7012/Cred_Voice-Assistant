# -*- coding: utf-8 -*-

import subprocess
import json
from typing import Dict

from app.rag.retriever import retrieve_context

# ----------------------------------
# Language mapping
# ----------------------------------
LANGUAGE_MAP = {
    "hi": "Hindi",
    "mr": "Marathi",
    "bn": "Bengali",
    "or": "Odia",
    "ta": "Tamil",
    "te": "Telugu",
    "en": "English"
}

# ----------------------------------
# Safe fallback (language aware)
# ----------------------------------
def fallback_response(language: str) -> str:
    if language == "mr":
        return "कृपया थोडी अधिक माहिती द्या जेणेकरून मी तुमची मदत करू शकेन."
    elif language == "bn":
        return "অনুগ্রহ করে আরও কিছু তথ্য দিন যাতে আমি আপনাকে সাহায্য করতে পারি।"
    elif language == "or":
        return "ଦୟାକରି ଅଧିକ ସୂଚନା ଦିଅନ୍ତୁ, ଯାହାଦ୍ୱାରା ମୁଁ ଆପଣଙ୍କୁ ସହଯୋଗ କରିପାରିବି।"
    elif language == "ta":
        return "தயவுசெய்து மேலும் விவரங்களை வழங்குங்கள்."
    elif language == "te":
        return "దయచేసి మరింత సమాచారం ఇవ్వండి."
    else:
        return "कृपया थोड़ी और जानकारी दें ताकि मैं आपकी मदद कर सकूं।"

# ----------------------------------
# Extract JSON safely from LLM output
# ----------------------------------
def extract_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None

# ----------------------------------
# MAIN PLANNER
# ----------------------------------
def llama_plan(
    user_text: str,
    language: str,
    memory: Dict
) -> Dict:
    """
    Planner responsibilities:
    - Decide tool
    - Extract facts
    - Use RAG context
    - NEVER hallucinate
    """

    language_name = LANGUAGE_MAP.get(language, "Hindi")

    # 1️⃣ Retrieve RAG context
    try:
        rag_context = retrieve_context(user_text)
    except Exception as e:
        print("RAG retrieval error:", e)
        rag_context = ""

    # 2️⃣ Planner prompt (STRICT)
    system_prompt = f"""
You are an AI Planner for a Voice-Based Government Welfare Assistant.

STRICT RULES:
- Respond ONLY in {language_name}
- Decide exactly ONE tool
- Extract facts if present (age, income, state)
- If scheme info is asked → scheme_retriever
- If eligibility is asked → eligibility_checker
- If explanation only → direct_answer
- DO NOT hallucinate schemes
- DO NOT ask for details if answer already exists

Return ONLY valid JSON.

User Memory:
{json.dumps(memory, ensure_ascii=False)}

Retrieved Scheme Context:
{rag_context if rag_context else "No scheme data found."}

User Query:
{user_text}

JSON FORMAT:
{{
  "tool": "scheme_retriever | eligibility_checker | direct_answer",
  "reason": "Answer in {language_name}",
  "facts_to_store": {{
    "age": null,
    "income": null,
    "state": null
  }}
}}
"""

    # 3️⃣ Ollama call (UTF-8 safe, retry)
    for attempt in range(2):
        try:
            process = subprocess.run(
                ["ollama", "run", "llama3:8b-instruct-q4_0"],
                input=system_prompt,
                text=True,
                encoding="utf-8",      # ✅ FIXES Unicode crash
                errors="ignore",
                capture_output=True,
                timeout=60
            )

            raw = process.stdout.strip()
            if not raw:
                continue

            plan = extract_json(raw)
            if plan is None:
                print("Invalid JSON from Ollama:", raw)
                continue

            # Safety defaults
            plan.setdefault("tool", "direct_answer")
            plan.setdefault("reason", fallback_response(language))
            plan.setdefault("facts_to_store", {})

            # 🔍 DEBUG (IMPORTANT)
            print("PLAN FROM LLM:", plan)

            return plan

        except subprocess.TimeoutExpired:
            print("Ollama timeout, retrying...")
            continue

        except Exception as e:
            print("Ollama error:", e)
            break

    # 4️⃣ Guaranteed safe fallback plan
    return {
        "tool": "direct_answer",
        "reason": fallback_response(language),
        "facts_to_store": {}
    }
