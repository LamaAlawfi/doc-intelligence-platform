from typing import Dict, Any, List, Tuple


REQUIRED_KEYS = [
    "title",
    "topic",
    "audience",
    "purpose",
    "assumptions",
    "executive_summary",
    "objectives",
    "main_content",
    "key_terms",
    "recommendations",
    "risks_and_considerations",
    "conclusion",
]


def validate_report(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # ---- Keys: exact & required ----
    for k in REQUIRED_KEYS:
        if k not in data:
            errors.append(f"Missing key: {k}")

    extra_keys = set(data.keys()) - set(REQUIRED_KEYS)
    if extra_keys:
        errors.append(f"Extra keys not allowed: {sorted(list(extra_keys))}")

    if errors:
        return False, errors

    # ---- Types ----
    if not isinstance(data["assumptions"], list):
        errors.append("assumptions must be a list.")
    if not isinstance(data["objectives"], list):
        errors.append("objectives must be a list.")
    if not isinstance(data["main_content"], list):
        errors.append("main_content must be a list of 3 sections.")
    if not isinstance(data["key_terms"], list):
        errors.append("key_terms must be a list.")
    if not isinstance(data["recommendations"], list):
        errors.append("recommendations must be a list.")
    if not isinstance(data["risks_and_considerations"], list):
        errors.append("risks_and_considerations must be a list.")

    # ---- Objectives ----
    if isinstance(data["objectives"], list) and len(data["objectives"]) != 3:
        errors.append("objectives must contain exactly 3 items.")
    if isinstance(data["objectives"], list):
        for i, obj in enumerate(data["objectives"]):
            if not isinstance(obj, str) or not obj.strip():
                errors.append(f"objectives[{i}] must be a non-empty string.")

    # ---- Executive summary lines (rough) ----
    if isinstance(data["executive_summary"], str):
        lines = [ln.strip() for ln in data["executive_summary"].splitlines() if ln.strip()]
        if not (4 <= len(lines) <= 6):
            errors.append("executive_summary should be 4–6 lines (use line breaks).")
    else:
        errors.append("executive_summary must be a string.")

    # ---- Main content ----
    mc = data["main_content"]
    if not isinstance(mc, list) or len(mc) != 3:
        errors.append("main_content must contain exactly 3 sections.")
    else:
        for i, sec in enumerate(mc):
            if not isinstance(sec, dict):
                errors.append(f"main_content[{i}] must be an object.")
                continue
            if "section_title" not in sec or "content" not in sec:
                errors.append(f"main_content[{i}] must have 'section_title' and 'content'.")
                continue

            title = sec.get("section_title")
            if not isinstance(title, str) or not title.strip():
                errors.append(f"main_content[{i}].section_title must be a non-empty string.")
            else:
                # enforce short title 3–6 words
                words = [w for w in title.strip().split() if w]
                if not (3 <= len(words) <= 6):
                    errors.append(f"main_content[{i}].section_title must be 3–6 words.")

            content = sec.get("content")
            if not isinstance(content, list):
                errors.append(f"main_content[{i}].content must be a list of bullet strings.")
            else:
                if not (4 <= len(content) <= 7):
                    errors.append(f"main_content[{i}].content must have 4–7 bullets.")
                for j, bullet in enumerate(content):
                    if not isinstance(bullet, str) or not bullet.strip():
                        errors.append(f"main_content[{i}].content[{j}] must be a non-empty string.")

    # ---- Key terms: 6–10 items with term/definition ----
    kt = data["key_terms"]
    if not isinstance(kt, list) or not (6 <= len(kt) <= 10):
        errors.append("key_terms must contain 6–10 items.")
    else:
        for i, item in enumerate(kt):
            if not isinstance(item, dict):
                errors.append(f"key_terms[{i}] must be an object.")
                continue
            if "term" not in item or "definition" not in item:
                errors.append(f"key_terms[{i}] must include 'term' and 'definition'.")
                continue
            if not isinstance(item["term"], str) or not item["term"].strip():
                errors.append(f"key_terms[{i}].term must be a non-empty string.")
            if not isinstance(item["definition"], str) or not item["definition"].strip():
                errors.append(f"key_terms[{i}].definition must be a non-empty string.")

    # ---- Recommendations / Risks counts ----
    rec = data["recommendations"]
    if not isinstance(rec, list) or not (3 <= len(rec) <= 5):
        errors.append("recommendations must contain 3–5 bullets.")
    else:
        for i, r in enumerate(rec):
            if not isinstance(r, str) or not r.strip():
                errors.append(f"recommendations[{i}] must be a non-empty string.")

    risks = data["risks_and_considerations"]
    if not isinstance(risks, list) or not (3 <= len(risks) <= 5):
        errors.append("risks_and_considerations must contain 3–5 bullets.")
    else:
        for i, r in enumerate(risks):
            if not isinstance(r, str) or not r.strip():
                errors.append(f"risks_and_considerations[{i}] must be a non-empty string.")

    # ---- Conclusion lines ----
    if isinstance(data["conclusion"], str):
        lines = [ln.strip() for ln in data["conclusion"].splitlines() if ln.strip()]
        if not (3 <= len(lines) <= 5):
            errors.append("conclusion should be 3–5 lines (use line breaks).")
    else:
        errors.append("conclusion must be a string.")

    return (len(errors) == 0), errors
