import os
import json
from langchain_openai import ChatOpenAI

REPORT_TEMPLATE = {
    "title": "",
    "topic": "",
    "audience": "General",
    "purpose": "",
    "assumptions": [],
    "executive_summary": "",
    "objectives": [],
    "main_content": [
        {"section_title": "", "content": []},
        {"section_title": "", "content": []},
        {"section_title": "", "content": []},
    ],
    "key_terms": [],
    "recommendations": [],
    "risks_and_considerations": [],
    "conclusion": ""
}

WRITER_PROMPT = """
You are a writing agent for a FIXED-template document generator.

NON-NEGOTIABLE:
- The JSON TEMPLATE is FIXED. Do not add/remove/rename keys. Do not change structure.
- Output STRICT JSON only. No markdown. No extra text.
- Do NOT invent precise facts (numbers, dates, company claims). If needed, write assumptions instead.
- Write in the requested language: {language}
- If plan includes "must_include", you MUST use every item at least once in main_content bullets or key_terms.


Return JSON that matches EXACTLY this template:
{template_json}

Planner plan (must guide what you write):
{plan_json}

You MUST obey plan.constraints and plan.quality_targets.

User request:
{user_input}

HARD CONSTRAINTS:
- objectives: exactly 3 items (action-oriented, not definitions)
- main_content: exactly 3 sections
- section_title must be SHORT (3–6 words), not full sentences
- section titles must closely follow plan.section_focus (same order and meaning)
- each main_content.content: 5–7 bullet strings (prefer 6–7 unless user request is very short)
- every bullet must contain at least ONE of:
  (a) a concrete workflow step (input → processing → output),
  (b) a practical example (e.g., hospital triage, fraud detection, call center),
  (c) an implementation detail (data needed, integration point, governance),
  (d) a decision/trade-off (accuracy vs interpretability, automation vs oversight)
- BAN vague bullets like "AI improves efficiency" unless immediately followed by "for example: ..."
- key_terms: 6–10 items, each item MUST be an object with keys: "term", "definition"
  and each definition must be 1–2 sentences maximum
- recommendations: 3–5 bullets, each must start with an action verb (Implement/Establish/Adopt/Monitor/etc.)
- risks_and_considerations: 3–5 bullets, each must include a mitigation hint (e.g., "Mitigation: ...")
- executive_summary: 4–6 lines separated by \\n (each line a complete sentence)
- conclusion: 3–5 lines separated by \\n (each line a complete sentence)
"""

def _safe_json_load(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise

def writer_agent(user_input: str, language: str, plan: dict, model_name: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or export it in terminal.")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,  # 🔥 lower = less generic
        api_key=api_key,
    )

    prompt = WRITER_PROMPT.format(
        language=language,
        template_json=json.dumps(REPORT_TEMPLATE, ensure_ascii=False),
        plan_json=json.dumps(plan, ensure_ascii=False),
        user_input=user_input,
    )

    out = llm.invoke(prompt).content
    return _safe_json_load(out)

