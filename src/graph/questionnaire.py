from typing import List, Dict, Any

def get_standard_questionnaire(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    file_options = [{"label": f["name"], "value": f["id"]} for f in files]
    
    return [
        {
            "id": "language",
            "type": "mcq",
            "question": "Q0) Select Document Language / اختر لغة الوثيقة",
            "options": ["Arabic / العربية", "English / الإنجليزية"]
        },
        {
            "id": "primary_files",
            "type": "multi_select",
            "question": "Q1) Which file(s) should be the main source for the new document?",
            "options": file_options
        },
        {
            "id": "scope_mode",
            "type": "mcq",
            "question": "Q2) Scope mode?",
            "options": [
                "1) Mostly based on 1 document",
                "2) Merge selected docs (2-3)",
                "3) Combine all docs",
                "4) Create new synthesized doc using all + my instructions"
            ]
        },
        {
            "id": "doc_type",
            "type": "mcq",
            "question": "Q3) Output doc type?",
            "options": [
                "Proposal", "Solution Overview", "Executive Summary", 
                "Technical Report", "SRS", "Meeting Brief", "Other"
            ]
        },
        {
            "id": "audience",
            "type": "mcq",
            "question": "Q4) Target audience?",
            "options": ["Client", "Management", "Technical Team", "Professor", "General"]
        },
        {
            "id": "tone",
            "type": "mcq",
            "question": "Q5) Tone?",
            "options": ["Formal", "Concise", "Detailed"]
        },
        {
            "id": "purpose",
            "type": "short_answer",
            "question": "Q6) Main purpose of this document?"
        },
        {
            "id": "must_include",
            "type": "short_answer",
            "question": "Q7) Must-include points / sections?"
        },
        {
            "id": "must_avoid",
            "type": "short_answer",
            "question": "Q8) Must-avoid points / sections?"
        },
        {
            "id": "length",
            "type": "mcq",
            "question": "Q9) Target length?",
            "options": ["1 page", "2-3 pages", "5+ pages", "Custom"]
        },
        {
            "id": "output_format",
            "type": "mcq",
            "question": "Q10) Output format?",
            "options": ["DOCX", "PDF", "MD", "TXT"]
        },
        {
            "id": "definitions_acronyms",
            "type": "short_answer",
            "question": "Q11) Provide any terms, acronyms, and their definitions (e.g., AI: Artificial Intelligence / الذكاء الاصطناعي)."
        },
        {
            "id": "reviewers",
            "type": "short_answer",
            "question": "Q12) Names and titles of reviewers (e.g., Ahmad - Director)."
        },
        {
            "id": "approvers",
            "type": "short_answer",
            "question": "Q13) Names and titles of approvers (e.g., Sarah - CEO)."
        },
        {
            "id": "bilingual_intro_concl",
            "type": "mcq",
            "question": "Q14) Keep Introduction and Conclusion bilingual (Arabic & English) regardless of main language selection?",
            "options": ["Yes / نعم", "No / لا"]
        },
        {
            "id": "classification",
            "type": "mcq",
            "question": "Q15) Document Classification?",
            "options": ["Public", "Internal", "Restricted", "Highly Confidential"]
        }
    ]
