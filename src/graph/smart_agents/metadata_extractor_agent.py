import json
import os
from src.generation.llm import call_llm

def metadata_extractor_agent(all_text: str, context: str = ""):
    """
    Extracts Definitions, Acronyms, and potentially Reviewers/Approvers 
    from the provided text.
    """
    prompt = f"""
You are a document analyzer. Your goal is to extract metadata from the provided source text 
to help populate an official government report.

== SOURCE TEXT (First 15,000 chars) ==
{all_text[:15000]}

== USER CONTEXT ==
{context}

== YOUR TASK ==
1. Extract all **Acronyms and Definitions** found in the text.
2. Identify any mentioned **Reviewers** or **Approvers** (names and job titles).
3. Identify the **Target Organization** and **Audience** if clear.

== OUTPUT FORMAT ==
You must return ONLY a JSON object with this structure:
{{
  "definitions": ["Acronym: Full Definition", "Term: Description"],
  "reviewers": ["Name - Title", "Name - Title"],
  "approvers": ["Name - Title"],
  "organization": "extracted name or null",
  "audience": "extracted audience or null"
}}

Ensure the formatting of definitions uses 'Term: Definition' and people use 'Name - Title' precisely.
If not found, return empty lists/null.
""".strip()

    messages = [
        {"role": "system", "content": "You are a precise data extraction agent."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw_res = call_llm(messages, json_mode=True)
        return json.loads(raw_res)
    except Exception as e:
        print(f"Metadata Extraction Error: {e}")
        return {
            "definitions": [],
            "reviewers": [],
            "approvers": [],
            "organization": None,
            "audience": None
        }
