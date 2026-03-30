import json
import re
from pathlib import Path

# =========================
# Template Logic Migration from "Templete Generator"
# =========================

SECTION_KEYWORDS = {
    "title": ["survey", "overview", "review", "framework", "agents", "llm"],
    "executive_summary": ["we propose", "this paper", "we present", "in this survey", "overview", "summary"],
    "background_and_context": ["background", "motivation", "context", "recent", "emerging", "challenge", "problem"],
    "objectives": ["objective", "goal", "aim", "we aim", "we focus", "purpose"],
    "key_findings": ["results", "findings", "we find", "show", "demonstrate", "outperform", "evaluation"],
    "analysis_and_insights": ["analysis", "insight", "discussion", "implication", "trade-off", "comparison"],
    "recommendations": ["recommend", "future work", "direction", "should", "we suggest", "guideline"],
    "risks_and_limitations": ["limitation", "risk", "challenge", "open problem", "safety", "bias", "hallucination"],
    "conclusion": ["conclusion", "in summary", "overall", "we conclude", "takeaway"],
}

def load_template(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))

def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sents = re.split(r"(?<=[.!?])\s+", text)
    sents = [s.strip() for s in sents if 40 <= len(s.strip()) <= 240]
    return sents

def score_sentence(sent: str, keywords: list[str]) -> int:
    s = sent.lower()
    score = 0
    for kw in keywords:
        if kw in s:
            score += 3
    if any(x in s for x in ["we", "this", "paper", "survey"]):
        score += 1
    return score

def pick_top_sentences(all_text: str, section: str, k: int) -> list[str]:
    keywords = SECTION_KEYWORDS.get(section, [])
    sents = split_sentences(all_text)

    ranked = sorted(
        ((score_sentence(s, keywords), s) for s in sents),
        key=lambda x: x[0],
        reverse=True,
    )

    chosen = []
    seen = set()

    for sc, s in ranked:
        if sc <= 0:
            continue
        norm = s.lower()
        if norm in seen:
            continue
        seen.add(norm)
        chosen.append(s)
        if len(chosen) == k:
            break

    # fallback: if not enough, take first available sentences
    if len(chosen) < k:
        for s in sents:
            norm = s.lower()
            if norm not in seen:
                chosen.append(s)
                seen.add(norm)
            if len(chosen) == k:
                break

    while len(chosen) < k:
        chosen.append("Not enough evidence found in the input files.")
    return chosen

def fill_template_baseline(template: dict, all_text: str) -> dict:
    """Takes a loaded template dict, and raw text, returns filled template."""
    filled = {}
    for section_name, section_obj in template.items():
        bullet_count = 3
        if isinstance(section_obj, dict):
            # Try to get number of items from 'bullets' list if it exists
            b = section_obj.get("bullets", [])
            if isinstance(b, list) and len(b) > 0:
                bullet_count = len(b)
        
        bullets = pick_top_sentences(all_text, section_name, bullet_count)
        filled[section_name] = {"bullets": bullets}
    return filled

import concurrent.futures

def fill_template_with_llm(topic: str, structure: dict, language: str = "Arabic", bilingual_intro_concl: bool = False) -> dict:
    """
    Fills a document structure using LLM knowledge based on a topic/context.
    Processes sections in parallel to avoid output token limits.
    """
    from src.generation.llm import call_llm
    
    filled_structure = {}
    
    def process_section(section_id, section_data):
        title = section_data.get("title", section_id)
        bullet_count = len(section_data.get("bullets", []))
        if bullet_count == 0:
            bullet_count = 3
            
        lang_mandate = f"You MUST write all content in perfect {language}."
        if bilingual_intro_concl and section_id.lower() in ["intro", "introduction", "concl", "conclusion"]:
            lang_mandate = "This section MUST be bilingual. Provide text in ARABIC followed by text in ENGLISH, clearly separated."

        role_context = "You are an expert government document writer."
        if "دليل المعلم" in title or "Teacher Guide" in title or "teacher" in section_id.lower():
            if language == "English":
                role_context = f"""You are an expert Curriculum Developer creating a Teacher Guide for a Saudi Ministry-style curriculum. You MUST write ALL content in formal English. You MUST format the output EXACTLY with these bold headers:
### Objectives
- (Clear, measurable behavioral and cognitive objectives)
### Expected Learning Outcomes
- (The student will be able to [action verb] [learning outcome])
### Teaching Steps
1. Introduction (xx minutes)
2. Explanation (xx minutes)
3. Activity (xx minutes)
4. Discussion (xx minutes)
### Time Allocation
*(MUST use a clean Markdown table with columns: Phase | Duration in Minutes)*
### Expected Answers
- (Solutions for exercises and the student file)
### Common Mistakes
*(MUST use a clean Markdown table with columns: Common Mistake | Correction Method)*
### Teacher Tips
- (Classroom management guidance)

*(If this is an Assessment/Review week, replace headers with Exam Key and Grading Rubric in English)*"""
            else:
                role_context = f"""You are an expert Curriculum Developer creating a Teacher Guide for a Saudi Ministry-style curriculum. You MUST write ALL content in formal Arabic. You MUST format the output EXACTLY with these bold headers:
### الأهداف
- (أهداف سلوكية ومعرفية واضحة وقابلة للقياس)
### نواتج التعلم المتوقعة
- (أن [فعل سلوكي] الطالب [نواتج التعلم المختارة])
### خطوات التدريس
1. المقدمة (xx دقيقة)
2. الشرح (xx دقيقة)
3. النشاط (xx دقيقة)
4. المناقشة (xx دقيقة)
### توزيع الوقت
*(MUST use a clean Markdown table with columns: المرحلة | المدة بالدقائق)*
### الإجابات المتوقعة
- (حلول لتمارين وملف الطالب)
### الأخطاء الشائعة
*(MUST use a clean Markdown table with columns: الخطأ الشائع | طريقة التصحيح)*
### نصائح للمعلم
- (توجيهات لإدارة الفصل)

*(If this is an Assessment/Review week, replace headers with Exam Key and Grading Rubric in Arabic)*"""
        elif "ملف الطالب" in title or "Student File" in title or "student" in section_id.lower():
            if language == "English":
                role_context = f"""You are an expert Educational Material Creator designing a Student File for a Saudi Ministry-style textbook. You MUST write ALL content in formal English. You MUST format the output EXACTLY with these bold headers:
### Learning Objectives
- (What the student will learn)
### Key Concepts
- (Core ideas)
### Explanation
- (Detailed, age-appropriate explanation with real academic value. If the subject is about AI, absolutely never mention programming or code)
### Examples
- (Realistic, practical examples)
### Activities
- (Interactive classroom or individual activities)
### Exercises
- (Practice questions of increasing difficulty)
### Assessment
- (Quick lesson assessment)

*(If this is an Assessment/Review week, replace headers with the Actual Exam Questions in English)*"""
            else:
                role_context = f"""You are an expert Educational Material Creator designing a Student File for a Saudi Ministry-style textbook. You MUST write ALL content in formal Arabic. You MUST format the output EXACTLY with these bold headers:
### أهداف التعلم
- (ما سيتعلمه الطالب)
### المفاهيم الرئيسية
- (الأفكار الأساسية)
### الشرح
- (شرح مفصل ومناسب لعمر الطالب، ذو قيمة علمية حقيقية غير مكررة. يمنع منعاً باتاً ذكر البرمجة أو الأكواد إذا كان الموضوع عن الذكاء الاصطناعي)
### الأمثلة
- (أمثلة واقعية وعملية)
### الأنشطة
- (أنشطة تفاعلية صفية أو فردية)
### التمارين
- (أسئلة تدريبية متدرجة الصعوبة)
### التقييم
- (تقييم سريع للدرس)

*(If this is an Assessment/Review week, replace headers with the Actual Exam Questions in Arabic)*"""
        prompt = f"""
{role_context}
Your task: Write the content for the section '{title}' based on the provided topic/context.

== TOPIC / CONTEXT ==
{topic}

== RULES ==
1. Write unique, highly detailed, structured academic content for this section based ONLY on the provided context. DO NOT repeat explanations from previous sections. Each week MUST build new knowledge. Use a mix of professional paragraphs, bullet points, and the requested Markdown tables. DO NOT use only bullet points.
   - For 'Examples', you MUST provide realistic, practical AI scenarios (like summarizing text, writing emails, asking for study help).
   - For 'Activities', you MUST provide varied and highly interactive tasks (e.g., comparing good vs bad prompts, fixing weak prompts, group competitions).
2. Use professional, formal educational language appropriate for the Saudi Ministry of Education guidelines. Write EXCLUSIVELY in formatting matching the headers above.
3. **LANGUAGE MANDATE**: {lang_mandate} ALL headers, ALL content, ALL bullet points MUST be in {language}. Do NOT mix languages.
4. Return ONLY a valid JSON object with a single key "bullets" containing a list of strings (each string is a paragraph, table, or bullet point): {{"bullets": ["...", "..."]}}
5. **CRITICAL HALLUCINATION BAN**: If the subject is "هندسة الأوامر" (Prompt Engineering), you MUST NEVER write anything about mathematical geometry (أشكال هندسية), nor programming loops/code (برمجة، طباعة متغبرات، حلقات تكرارية). The topic is EXCLUSIVELY how to interact with AI Chatbots, write effective text prompts, and analyze AI responses. Your content MUST be 100% about AI prompt formulation.
""".strip()
        
        messages = [
            {"role": "system", "content": "You are a professional government analyst."}, 
            {"role": "user", "content": prompt}
        ]
        
        try:
            raw_res = call_llm(messages, json_mode=True)
            res_json = json.loads(raw_res)
            return section_id, res_json
        except Exception as e:
            return section_id, {"bullets": [f"[Generation Error] Could not process section: {str(e)}"]}
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for section_id, section_data in structure.items():
            futures.append(executor.submit(process_section, section_id, section_data))
            
        for future in concurrent.futures.as_completed(futures):
            sec_id, res = future.result()
            filled_structure[sec_id] = res
            
    ordered_filled_structure = {k: filled_structure[k] for k in structure.keys() if k in filled_structure}
    return ordered_filled_structure
