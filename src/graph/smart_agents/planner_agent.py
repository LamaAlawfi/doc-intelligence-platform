import json
import os
from langchain_openai import ChatOpenAI

PLANNER_PROMPT = """
You are a planning agent for a FIXED-template document generator.

NON-NEGOTIABLE:
- The document TEMPLATE is fixed and must never change.
- You must NOT write the document content. You only produce a plan.
- Output STRICT JSON only (no markdown, no extra text).
- Write all field values in the same language as the user's request.

Return JSON with EXACTLY these keys:
{{
  "topic": "string",
  "audience": "string (infer if possible, else 'General')",
  "purpose": "string (1 sentence, specific)",
  "tone": "string (professional | academic | executive | marketing)",
  "assumptions": ["string", "..."],
  "section_focus": [
    "Section 1 focus (intro/foundation) - specific to the topic",
    "Section 2 focus (core/details) - specific to the topic",
    "Section 3 focus (applications/next steps/risks) - specific to the topic"
  ],
  "constraints": [
    "Do not invent precise facts or numbers",
    "Keep it suitable for the inferred audience",
    "Use practical, actionable language"
  ],
  "quality_targets": {{
    "summary_lines": "4-6",
    "objectives_count": 3,
    "main_sections_count": 3,
    "key_terms_count_range": "6-10",
    "recommendations_count_range": "3-5",
    "risks_count_range": "3-5"
  }}
}}

User request:
{user_input}

Language hint: {language}

Planning guidelines:
- If the request is vague, add assumptions (do not ask questions).
- Make section_focus concrete and non-generic.
"""

def planner_agent(user_input: str, language: str, model_name: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or export it in terminal.")

    llm = ChatOpenAI(model=model_name, temperature=0.2, api_key=api_key)

    prompt = PLANNER_PROMPT.format(user_input=user_input, language=language)
    out = llm.invoke(prompt).content.strip()

    try:
        return json.loads(out)
    except json.JSONDecodeError:
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(out[start:end + 1])
        raise
