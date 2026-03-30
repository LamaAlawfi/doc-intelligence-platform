# src/agents/repair_agent.py
import os
import json
from langchain_openai import ChatOpenAI
from .writer_agent import REPORT_TEMPLATE  # reuse the fixed template


REPAIR_PROMPT = """
You are a JSON repair agent for a FIXED-template document generator.

NON-NEGOTIABLE:
- Output MUST be valid JSON only. No markdown. No extra text.
- Do NOT add/remove/rename keys. Match the template EXACTLY.
- Fix ONLY what is required by the validation errors.
- Keep the language: {language}
- Do NOT invent precise facts (numbers, dates, claims). Use assumptions if needed.
- For executive_summary and conclusion, you MUST use line breaks so each line is on a separate line.
  That means executive_summary must contain 4–6 lines separated by \\n,
  and conclusion must contain 3–5 lines separated by \\n.

Template (must match exactly):
{template_json}

Planner plan:
{plan_json}

User request:
{user_input}

Broken JSON:
{broken_json}

Validation errors:
{errors_json}

Return the corrected JSON only.
"""


def _safe_json_load(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # fallback: extract first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def repair_agent(
    user_input: str,
    language: str,
    plan: dict,
    broken: dict,
    errors: list,
    model_name: str
) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or export it in terminal.")

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,
        api_key=api_key
    )

    prompt = REPAIR_PROMPT.format(
        language=language,
        template_json=json.dumps(REPORT_TEMPLATE, ensure_ascii=False),
        plan_json=json.dumps(plan, ensure_ascii=False),
        user_input=user_input,
        broken_json=json.dumps(broken, ensure_ascii=False),
        errors_json=json.dumps(errors, ensure_ascii=False),
    )

    out = llm.invoke(prompt).content
    return _safe_json_load(out)

