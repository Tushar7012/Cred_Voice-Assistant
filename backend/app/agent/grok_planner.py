import os
import json
import requests
from typing import Dict
from app.rag.retriever import retrieve_context

GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"  

LANGUAGE_MAP = {
    "hi": "Hindi",
    "mr": "Marathi",
    "or": "Odia",
    "bn": "Bengali",
    "en": "English"
}

def fallback_response(language: str) -> str:
    return "मुझे इस प्रश्न का उत्तर अभी उपलब्ध नहीं है।"

def extract_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None

def grok_plan(user_text: str, language: str, memory: Dict) -> Dict:
    language_name = LANGUAGE_MAP.get(language, "Hindi")

    try:
        rag_context = retrieve_context(user_text)
    except Exception:
        rag_context = ""

    system_prompt = f"""
You are an intelligent AI planner.

Rules:
- Answer in {language_name} only
- Government schemes → structured explanation
- GK / History / Geography → direct factual answer
- If unknown → clearly say you don't know
- Output ONLY valid JSON

User Memory:
{json.dumps(memory, ensure_ascii=False)}

Context:
{rag_context}

User Query:
{user_text}

JSON FORMAT:
{{
  "tool": "scheme_retriever | eligibility_checker | direct_answer",
  "reason": "clear answer in {language_name}",
  "facts_to_store": {{
    "age": null,
    "income": null,
    "state": null
  }}
}}
"""

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-2-latest",
        "messages": [
            {"role": "system", "content": system_prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(
            GROK_API_URL,
            headers=headers,
            json=payload,
            timeout=40
        )

        data = response.json()
        raw = data["choices"][0]["message"]["content"]

        plan = extract_json(raw)
        if plan is None:
            print("Invalid JSON from Grok:", raw)
            return {
                "tool": "direct_answer",
                "reason": fallback_response(language),
                "facts_to_store": {}
            }

        print("PLAN FROM GROK:", plan)

        plan.setdefault("tool", "direct_answer")
        plan.setdefault("reason", fallback_response(language))
        plan.setdefault("facts_to_store", {})

        return plan

    except Exception as e:
        print("Grok error:", e)
        return {
            "tool": "direct_answer",
            "reason": fallback_response(language),
            "facts_to_store": {}
        }
