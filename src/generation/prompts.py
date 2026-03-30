"""
Evidence-aware prompts with structured JSON outputs.
All prompts enforce citation discipline and source grounding.
"""
from typing import Dict, List, Any
import json
import logging

from src.generation.llm import call_llm
from src.generation.schemas import (
    OutlineResponse,
    SectionWriterResponse,
    TemplateGeneratorResponse,
    parse_and_validate_outline,
    parse_and_validate_section,
    parse_and_validate_template,
    validate_outline_for_doc_type,
)

logger = logging.getLogger(__name__)

# ── Template Anchors ─────────────────────────────────────────────────────────
# Keys MUST match doc_spec["type"] exactly (from UI)
TEMPLATE_ANCHORS = {
    "Proposal": [
        "Executive Summary",
        "Background / Context",
        "Problem Statement",
        "Scope",
        "Objectives",
        "Deliverables",
        "Timeline",
        "Risks & Mitigation",
        "Conclusion / Next Steps",
    ],
    "Solution Overview": [
        "Problem",
        "Proposed Solution",
        "Benefits",
        "High-Level Approach",
        "Risks",
        "Next Steps",
    ],
    "Executive Summary": [
        "Purpose / Scope",
        "Key Insights",
        "Recommendations",
        "Risks",
    ],
    "Technical Report": [
        "Introduction",
        "Background / Context",
        "Key Themes",
        "Implementation Considerations",
        "Risks & Constraints",
        "Recommendations / Next Steps",
    ],
    "Policy Brief": [
        "Issue Overview",
        "Evidence Summary",
        "Policy Options",
        "Recommendation",
        "Implementation Considerations",
        "Risks & Trade-offs",
    ],
    "Invoice": [
        "Client & Invoice Details",
        "Line Items",
        "Subtotal / Taxes / Total",
        "Payment Terms",
    ],
    "Letter": [
        "Greeting",
        "Purpose",
        "Main Message",
        "Closing",
        "Signature",
    ],
    "Meeting Brief": [
        "Meeting Context",
        "Agenda",
        "Key Discussion Points",
        "Decisions",
        "Action Items",
        "Open Questions",
    ],
}

# ── Outline Prompt ───────────────────────────────────────────────────────────

OUTLINE_PROMPT = """You are a Document Architect. Create a precise outline grounded in the provided context.

== INPUTS ==
DOCUMENT SPEC:
{doc_spec}

PRIMARY SOURCES ({source_count} total):
{source_context}

SOURCE ROLES:
{source_roles}

{ref_template_section}

== RULES ==
1) Use the chosen Document Type requirements.
2) Do NOT invent facts "from sources" — if you mention source facts, they must be traceable to the source context.
3) Each section MUST include:
   - required_sources: ["source_1", ...] (can be empty only if knowledge_mode == "model_only")
   - must_include_from_sources: {{"source_1": "..."}}
4) Generate 3–5 deterministic search_queries per section (even in hybrid; can be generic in model_only).
5) min_evidence_chunks >= 2 for grounded/hybrid; can be 0 for model_only.
6) If a REFERENCE TEMPLATE is provided: use it ONLY for structure; do not copy facts unless present in sources.
7) **LANGUAGE MATCHING MANDATE**: You MUST write the `heading`, `description`, and `expected_outputs` in the selected DOCUMENT LANGUAGE: {language}.
8) **BILINGUAL OVERRIDE**: If the section is an "Introduction" or "Conclusion" AND `bilingual_intro_concl` is True, you MUST provide instructions for the writer to generate both Arabic and English text for this section.
{template_instruction}

== OUTPUT ==
Return ONLY valid JSON:
{{
  "title": "...",
  "sections": [
    {{
      "heading": "...",
      "description": "...",
      "required_sources": ["source_1", "source_2"],
      "search_queries": ["q1","q2","q3"],
      "min_evidence_chunks": 2,
      "expected_outputs": "...",
      "must_include_from_sources": {{"source_1":"phrase","source_2":"phrase"}}
    }}
  ]
}}
"""

TEMPLATE_ANCHOR_INSTRUCTION = """
TEMPLATE REQUIREMENT: Because the document type is "{doc_type}", you MUST use these section headings in order:
{anchored_headings}
You may add 1–2 optional sections AFTER these if the sources warrant it.
"""

# ── Section Writer Prompts (Knowledge Modes) ─────────────────────────────────

SECTION_WRITER_PROMPT_GROUNDED = """You are an expert Government & Corporate Technical Writer. Write the official section body.
DO NOT MERELY SUMMARIZE OR COPY-PASTE the evidence. You must SYNTHESIZE the facts into a highly professional, beautifully formatted, and extrapolative narrative that fits the Section Heading.

== SECTION ==
Heading: {heading}
Goal: {description}

== EVIDENCE PACK ==
Each item has a cite_id you MUST reference in brackets when using that evidence.
{structured_evidence}

== SPEC ==
Tone: {tone}
Audience: {audience}

== HARD RULES ==
1) DO NOT REGURGITATE. Write original, professional paragraphs that weave the evidence together logically.
2) Use ONLY the evidence pack above. No invented facts, but original framing and professional phrasing are required.
3) Cite using the exact cite_id in brackets for every major claim, e.g. [S1:fileA_C003]. Every paragraph MUST contain at least 1 citation.
4) Formulate the output clearly using markdown bullet points, bolding for emphasis, and structured paragraphs.
5) If less than {min_evidence} evidence items are provided, output ONLY:
   {{"section_body":"INSUFFICIENT EVIDENCE","citations_used":[],"conflict_detected":false,"conflict_description":null,"missing_info":"<missing>","followup_question":"<1 question>"}}
6) **LANGUAGE OUTPUT MANDATE**: You MUST write the final output in the selected DOCUMENT LANGUAGE: {language}.
7) **BILINGUAL EXCEPTION**: If the section is "Introduction" or "Conclusion" AND `bilingual_intro_concl` is True, you MUST write the content in BOTH Arabic and English, clearly separated by headers (e.g., "--- ARABIC / العربية ---" and "--- ENGLISH / الإنجليزية ---").
8) **Multi-Source Conflict**: If evidence from two different sources contradicts each other:
   - DO NOT WRITE the section body. Set `section_body` to "CONFLICT DETECTED. AWAITING HUMAN RESOLUTION."
   - Set `conflict_detected` to true.
   - Set `conflict_description` to a detailed explanation of the conflicting facts IN THE MATCHING LANGUAGE.

== OUTPUT (JSON only) ==
{{
  "section_body": "...",
  "citations_used": ["S1:..."],
  "conflict_detected": false,
  "conflict_description": null,
  "missing_info": null,
  "followup_question": null
}}
"""

SECTION_WRITER_PROMPT_HYBRID = """You are an expert Government & Corporate Technical Writer.
DO NOT MERELY SUMMARIZE OR COPY-PASTE the evidence. SYNTHESIZE the facts and augment them with industry best practices to build a robust, professional section.

== SECTION ==
Heading: {heading}
Goal: {description}

== EVIDENCE PACK ==
Each item has a cite_id you MUST reference in brackets when using that evidence.
{structured_evidence}

== SPEC ==
Tone: {tone}
Audience: {audience}

== HARD RULES ==
1) DO NOT REGURGITATE. Write original, highly formulated paragraphs that synthesize the evidence and extrapolate best practices.
2) You MUST cite the evidence pack for any claim that is presented as coming from the uploaded sources.
3) You MAY add general best-practice content to fill gaps (label it explicitly as "(General best practice)").
4) Do NOT cite "general best practice" content with source cite_ids.
5) Every paragraph should contain at least 1 citation OR explicitly be labeled as "(General best practice)". Use markdown bullets and bold text for high readability.
6) **LANGUAGE OUTPUT MANDATE**: You MUST write the final output in the selected DOCUMENT LANGUAGE: {language}.
7) **BILINGUAL EXCEPTION**: If the section is "Introduction" or "Conclusion" AND `bilingual_intro_concl` is True, you MUST write the content in BOTH Arabic and English, clearly separated by headers (e.g., "--- ARABIC / العربية ---" and "--- ENGLISH / الإنجليزية ---").
8) **Multi-Source Conflict**: If evidence from two different sources contradicts each other:
   - DO NOT WRITE the section body. Set `section_body` to "CONFLICT DETECTED. AWAITING HUMAN RESOLUTION."
   - Set `conflict_detected` to true.
   - Set `conflict_description` to a detailed explanation of the conflicting facts IN THE MATCHING LANGUAGE.

== OUTPUT (JSON only) ==
{{
  "section_body": "...",
  "citations_used": ["S1:..."],
  "conflict_detected": false,
  "conflict_description": null,
  "missing_info": null,
  "followup_question": null
}}
"""

SECTION_WRITER_PROMPT_MODEL_ONLY = """You are an expert Government & Corporate Technical Writer. Generate the section from broad knowledge and best practices.
You MUST write a highly structured, professional narrative. Avoid simplistic bullet lists; build a rich, extrapolative section.

== SECTION ==
Heading: {heading}
Goal: {description}

== SPEC ==
Tone: {tone}
Audience: {audience}

== RULES ==
1) No citations required. Weave a cohesive analysis.
2) Provide rich formatting: bold text, nested bullet points, and strong paragraph topics.
3) Do NOT pretend you used any uploaded sources.
4) **LANGUAGE MATCHING MANDATE**: You MUST write the final output (`section_body`) in the selected DOCUMENT LANGUAGE: {language}.
5) **BILINGUAL EXCEPTION**: If the section is "Introduction" or "Conclusion" AND `bilingual_intro_concl` is True, you MUST write the content in BOTH Arabic and English, clearly separated by headers (e.g., "--- ARABIC / العربية ---" and "--- ENGLISH / الإنجليزية ---").

== OUTPUT (JSON only) ==
{{
  "section_body": "...",
  "citations_used": [],
  "missing_info": null,
  "followup_question": null
}}
"""

# ── Template Generation Prompts ──────────────────────────────────────────────

TEMPLATE_GENERATION_PROMPT = """You are a Senior Government Document Architect. Create a professional document structure based on the user's topic.

== TOPIC / DOMAIN ==
{topic}

== TARGET MODE ==
{mode}

== MODE-SPECIFIC ARCHITECTURE RULES ==
- **IF '{mode}' == 'Executive Summary Mode'**:
    - Focus on strategic vision, high-level impact, and key recommendations.
    - Keep the structure lean (5-6 sections maximum).
    - Avoid deep technical or audit details that might overwhelm a Minister or CEO.
    - Mandatory Sections: 'Executive Summary', 'Strategic Vision', 'Key Recommendations', 'Expected Outcomes', 'High-Level Implementation Map'.

- **IF '{mode}' == 'Strategic Compliance Mode'**:
    - Focus on regulatory alignment, risk frameworks, and detailed technical methodologies.
    - Provide an EXHAUSTIVE, ULTRA-DENSE, MASSIVE structure (**25-35 granular sections**).
    - Break every theme down into microscopic sub-sections (e.g., instead of 'Risk', use 'Strategic Risk', 'Operational Risk', 'Cyber Risk', 'Financial Risk', 'Compliance Risk', 'Reputational Risk').
    - Mandatory Sections: 'Title Page', 'Introduction', 'Executive Summary', 'Regulatory & Legal Framework', 'Detailed Technical Methodology', 'Comprehensive Risk Assessment', 'Data Governance & Compliance', 'System Architecture Details', 'Audit & Verification Plan', 'Operational Continuity', 'Implementation Roadmap', 'Maintenance Strategy', 'Budgetary Impact', 'Future Outlook', 'Governance Sign-off', 'Conclusion'.

- **IF '{mode}' == 'Technical Solution Design'**:
    - Focus on system architecture, data flow, engineering stacks, and algorithmic detail.
    - Provide an EXTREMELY DETAILED technical structure (**20-30 deep technical sections**).
    - Mandatory Sections: 'Introduction', 'Project Overview', 'Problem Statement', 'Literature Review & Benchmarking', 'Emerging Technologies Research' (AI/ML models, algorithms), 'Solution Architecture Overview', 'Detailed Data Architecture' (Historical, Real-time, Performance, Input processing), 'Technical Stack & Infrastructure' (Programming, Databases, Cloud), 'Hardware & Networking', 'Concept Design & Prototyping', 'Functional Requirements', 'Non-Functional Requirements', 'API & Integration Strategy', 'Security & Encryption Framework', 'Implementation Strategy', 'Technical Risk & Mitigation', 'Conclusion'.

- **IF '{mode}' == 'Curriculum Mode'**:
    - Focus on creating a strictly ordered, highly academic curriculum spanning EXACTLY 16 WEEKS (producing exactly 32 paired sections).
    - You MUST divide the 16 weeks into 4 distinct Units strictly following this pattern:
        * Unit 1 (Weeks 1-4): Weeks 1,2,3 are lessons. Week 4 is Review/Assessment.
        * Unit 2 (Weeks 5-8): Weeks 5,6,7 are lessons. Week 8 is Midterm Assessment.
        * Unit 3 (Weeks 9-12): Weeks 9,10,11 are lessons. Week 12 is Review.
        * Unit 4 (Weeks 13-16): Weeks 13,14 are practical application assignments (e.g., using AI to summarize lessons or write emails). Week 15 is Review. Week 16 is the Final Project where students MUST use AI to create a real output (a report, presentation, or educational content) by applying their prompt engineering skills and improving prompts step-by-step. Make project instructions clear and structured.
    - **CRITICAL HALLUCINATION BAN**: If the subject is "هندسة الأوامر" (Prompt Engineering), you MUST NEVER confuse it with mathematical geometry (هندسة) or programming loops (أوامر). YOU MUST NEVER include code, variables, if-statements, print functions, algorithms, geometry, or math. The ENTIRE curriculum MUST exclusively teach writing and optimizing text prompts for Generative AI (Chatbots like ChatGPT).
    - For EVERY week (1 through 16 sequentially), you MUST generate TWO sequential sections.
    - **IF {language} is Arabic**, use Arabic titles and bullets:
        1. `"teacher_week_1": {{"title": "دليل المعلم: الأسبوع 1 - [اسم الوحدة] - [عنوان الدرس]", "bullets": ["الأهداف", "خطوات التدريس", "توزيع الوقت", "الإجابات المتوقعة", "الأخطاء الشائعة", "نصائح للمعلم"]}}`
        2. `"student_week_1": {{"title": "ملف الطالب: الأسبوع 1 - [اسم الوحدة] - [عنوان الدرس]", "bullets": ["أهداف التعلم", "المفاهيم الرئيسية", "الشرح", "الأمثلة", "الأنشطة", "التمارين", "التقييم"]}}`
    - **IF {language} is English**, use FULLY ENGLISH titles and bullets (DO NOT USE ANY ARABIC):
        1. `"teacher_week_1": {{"title": "Teacher Guide: Week 1 - [Unit Name] - [Lesson Title]", "bullets": ["Objectives", "Teaching Steps", "Time Allocation", "Expected Answers", "Common Mistakes", "Teacher Tips"]}}`
        2. `"student_week_1": {{"title": "Student File: Week 1 - [Unit Name] - [Lesson Title]", "bullets": ["Learning Objectives", "Key Concepts", "Explanation", "Examples", "Activities", "Exercises", "Assessment"]}}`
    - The curriculum MUST perfectly replicate the structure of an official Saudi Ministry of Education document written purely in {language}. ENSURE PROGRESSION: Do not repeat basic concepts; every week must introduce completely new knowledge.

== GENERAL RULES ==
1) Include administrative headers: 'Classification Status', 'Organization', 'Department', 'Version Number'. EXPLICITLY extract the 'color_theme' from the user chat history (e.g. 'green', 'red', 'blue', 'gray') and add it to the metadata.
2) For each section, specify a snake_case name, a title, and extraction bullets (3-6 per section).
3) **LENGTH SCALING MANDATE**: The requested "Target Page Length" or "TARGET PAGE COUNT" is critical. 
   - 1-2 pages: 5-7 sections.
   - 3-5 pages: 8-12 sections.
   - 6-9 pages: 12-18 sections.
   - 10-15+ pages: 20-30 exhaustive, granular sub-sections. You MUST break down major themes into multiple sub-sections to ensure the document is massive and authoritative.
4) **MANDATORY SECTIONS**: For Strategic/Technical modes, every document MUST start with an 'Introduction' and end with a 'Conclusion' section. (This rule is EXEMPT for 'Curriculum Mode').
5) **DATA-DRIVEN GENERATION**: If "Source Context" is provided, build your outline around the EXACT themes, facts, and entities found in that context. Do not invent generic sections if specific data exists.
6) **STRICT LANGUAGE MANDATE**: You MUST write ALL output (`doc_type`, `title`, `bullets`, `actual_content_preview`) STRICTLY in {language}. If {language} is English, DO NOT write ANY Arabic text. If {language} is Arabic, DO NOT write ANY English text. Only the JSON structure keys remain in English.
7) **BILINGUAL OVERRIDE**: If `bilingual_intro_concl` is True, the 'Introduction' and 'Conclusion' sections MUST have descriptions instructing the writer to produce bilingual content (Arabic and English side-by-side or sequential).

== OUTPUT (JSON only) ==
{{
  "doc_type": "Official Title",
  "metadata": {{
    "classification": "INTERNAL / RESTRICTED",
    "version": "1.0",
    "owner_dept": "...",
    "color_theme": "green"
  }},
  "structure": {{
    "section_name": {{ 
        "title": "Section Title", 
        "bullets": ["bullet_1", "bullet_2", "bullet_3"],
        "actual_content_preview": ["Insight 1: ...", "Insight 2: ..."] 
    }},
    ...
  }}
}}
"""

# ── Q&A Prompts ──────────────────────────────────────────────────────────────

QA_PROMPT_GROUNDED = """You are a helpful assistant. Answer using ONLY the evidence pack.

QUESTION:
{question}

EVIDENCE PACK (cite_id required):
{structured_evidence}

RULES:
- Use ONLY the evidence pack.
- Cite with [cite_id] for each major claim.
- If evidence is insufficient, say so and ask 1 follow-up question.

OUTPUT (JSON only):
{{
  "answer": "...",
  "citations_used": ["S1:..."],
  "followup_question": null
}}
"""

QA_PROMPT_MODEL_ONLY = """You are a helpful assistant. Answer using general knowledge.

QUESTION:
{question}

RULES:
- No citations required.

OUTPUT (JSON only):
{{
  "answer": "...",
  "citations_used": [],
  "followup_question": null
}}
"""

# ── Helpers ─────────────────────────────────────────────────────────────────

def build_source_context(primary_file_ids: List[str], file_index: List[Dict[str, Any]], file_id_to_src: Dict[str, str]) -> str:
    lines = []
    for fid in primary_file_ids:
        item = next((f for f in file_index if f["file_id"] == fid), None)
        if not item:
            continue
        src_label = file_id_to_src.get(fid, fid)
        keywords = ", ".join(item.get("keywords", []))
        preview = (item.get("preview", "") or "")[:1000]
        lines.append(
            f"- [{src_label}]:\n"
            f"  Keywords: {keywords}\n"
            f"  Evidence snippet: \"{preview}\""
        )
    return "\n".join(lines) if lines else "(no source context available)"


def format_evidence_for_writer(evidence_pack: List[Dict[str, Any]], file_id_to_src: Dict[str, str]) -> str:
    lines = []
    for ec in evidence_pack:
        fid = ec.get("file_id", "unknown")
        src_label = file_id_to_src.get(fid, "SX")
        src_short = src_label.replace("source_", "S") if src_label.startswith("source_") else src_label
        chunk_id = ec.get("chunk_id", "unknown")
        cite_id = f"{src_short}:{chunk_id}"
        text = ec.get("text", "")
        lines.append(
            f"- cite_id: [{cite_id}]\n"
            f"  file_source: {src_short}\n"
            f"  text: \"{text}\""
        )
    return "\n".join(lines) if lines else "(no evidence provided)"


# ── Public API ───────────────────────────────────────────────────────────────

def generate_outline(
    doc_spec: Dict[str, Any],
    source_context: str,
    source_roles: str = "",
    ref_template_context: str = "",
    source_count: int = 1,
    doc_type: str = "",
) -> OutlineResponse:
    template_instruction = ""
    if doc_type in TEMPLATE_ANCHORS:
        headings_str = "\n".join([f"- {h}" for h in TEMPLATE_ANCHORS[doc_type]])
        template_instruction = TEMPLATE_ANCHOR_INSTRUCTION.format(
            doc_type=doc_type,
            anchored_headings=headings_str,
        )

    ref_template_section = ""
    mimicry_rule = "The outline must adapt to uploaded topics."
    if ref_template_context:
        ref_template_section = f"== REFERENCE TEMPLATE (STRUCTURAL GUIDE) ==\n{ref_template_context}"
        mimicry_rule = (
            "STRUCTURAL CLONE REQUIRED: follow the reference template structure exactly."
        )

    prompt_text = OUTLINE_PROMPT.format(
        doc_spec=json.dumps(doc_spec, indent=2),
        source_context=source_context,
        source_roles=source_roles,
        ref_template_section=ref_template_section,
        mimicry_rule=mimicry_rule,
        source_count=source_count,
        template_instruction=template_instruction,
        language=doc_spec.get("language", "Arabic"),
        bilingual_intro_concl=doc_spec.get("bilingual_intro_concl", False),
    )

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON."},
        {"role": "user", "content": prompt_text},
    ]

    raw = call_llm(messages, json_mode=True)
    try:
        outline = parse_and_validate_outline(raw)
        validate_outline_for_doc_type(outline, doc_type or doc_spec.get("type", ""))
        return outline
    except Exception as e1:
        logger.warning("Outline parse/validation failed: %s — retrying once", e1)

    messages.append({"role": "assistant", "content": raw})
    messages.append({
        "role": "user",
        "content": "Fix and return ONLY valid JSON matching the required schema.",
    })
    raw2 = call_llm(messages, json_mode=True)
    outline2 = parse_and_validate_outline(raw2)
    validate_outline_for_doc_type(outline2, doc_type or doc_spec.get("type", ""))
    return outline2


def write_section(
    heading: str,
    description: str,
    evidence_pack: List[Dict[str, Any]],
    file_id_to_src: Dict[str, str],
    tone: str,
    audience: str,
    min_evidence: int = 2,
    knowledge_mode: str = "grounded",
    language: str = "Arabic",
    bilingual_intro_concl: bool = False,
) -> SectionWriterResponse:
    structured_evidence = format_evidence_for_writer(evidence_pack, file_id_to_src)

    if knowledge_mode == "model_only":
        prompt_text = SECTION_WRITER_PROMPT_MODEL_ONLY.format(
            heading=heading, description=description, tone=tone, audience=audience,
            language=language, bilingual_intro_concl=bilingual_intro_concl
        )
    elif knowledge_mode == "hybrid":
        prompt_text = SECTION_WRITER_PROMPT_HYBRID.format(
            heading=heading, description=description, structured_evidence=structured_evidence,
            tone=tone, audience=audience, min_evidence=min_evidence,
            language=language, bilingual_intro_concl=bilingual_intro_concl
        )
    else:
        prompt_text = SECTION_WRITER_PROMPT_GROUNDED.format(
            heading=heading, description=description, structured_evidence=structured_evidence,
            tone=tone, audience=audience, min_evidence=min_evidence,
            language=language, bilingual_intro_concl=bilingual_intro_concl
        )

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON."},
        {"role": "user", "content": prompt_text},
    ]

    raw = call_llm(messages, json_mode=True)
    try:
        return parse_and_validate_section(raw)
    except Exception as e1:
        logger.warning("Section parse failed for '%s': %s — retrying once", heading, e1)

    messages.append({"role": "assistant", "content": raw})
    messages.append({"role": "user", "content": "Fix and return ONLY valid JSON with the required fields."})
    raw2 = call_llm(messages, json_mode=True)
    return parse_and_validate_section(raw2)


def answer_question(
    question: str,
    evidence_pack: List[Dict[str, Any]],
    file_id_to_src: Dict[str, str],
    knowledge_mode: str,
) -> Dict[str, Any]:
    if knowledge_mode == "model_only" or not evidence_pack:
        prompt_text = QA_PROMPT_MODEL_ONLY.format(question=question)
    else:
        structured = format_evidence_for_writer(evidence_pack, file_id_to_src)
        prompt_text = QA_PROMPT_GROUNDED.format(question=question, structured_evidence=structured)

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON."},
        {"role": "user", "content": prompt_text},
    ]
    raw = call_llm(messages, json_mode=True)
    return json.loads(raw)


def generate_template(topic: str, mode: str = "Executive Summary Mode", language: str = "Arabic", bilingual_intro_concl: bool = False) -> TemplateGeneratorResponse:
    prompt_text = TEMPLATE_GENERATION_PROMPT.format(
        topic=topic, mode=mode, language=language, bilingual_intro_concl=bilingual_intro_concl
    )

    messages = [
        {"role": "system", "content": "Return ONLY valid JSON matching the requested template schema."},
        {"role": "user", "content": prompt_text},
    ]

    raw = call_llm(messages, json_mode=True)
    try:
        return parse_and_validate_template(raw)
    except Exception as e:
        logger.warning("Template generation failed: %s — retrying once", e)
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": "Fix and return ONLY valid JSON."})
        raw2 = call_llm(messages, json_mode=True)
        return parse_and_validate_template(raw2)
