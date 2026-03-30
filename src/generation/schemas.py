"""
Pydantic schemas for structured LLM outputs.
Enforces strict validation on outline and section writer responses.
"""
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator


# ── Outline Schemas ──────────────────────────────────────────────────────────

class OutlineSection(BaseModel):
    heading: str = Field(..., min_length=3, description="Section heading")
    description: str = Field(..., min_length=5, description="What this section covers")

    # Allow empty required_sources for model_only mode
    required_sources: List[str] = Field(
        default_factory=list,
        description="Source labels that MUST be cited (e.g. ['source_1', 'source_2'])"
    )

    search_queries: List[str] = Field(
        ..., min_length=3, max_length=5,
        description="Deterministic queries to retrieve evidence"
    )

    min_evidence_chunks: int = Field(
        default=2, ge=0,
        description="Minimum chunks required before writing"
    )

    expected_outputs: str = Field(
        ..., min_length=3,
        description="What the section should produce (e.g. 'summary of findings')"
    )

    must_include_from_sources: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-source phrases that MUST appear (e.g. {'source_1': 'key phrase'})"
    )


class OutlineResponse(BaseModel):
    title: str = Field(..., min_length=3, description="Document title")
    sections: List[OutlineSection] = Field(..., min_length=2, description="Ordered list of sections")

    @field_validator("sections")
    @classmethod
    def sections_must_have_headings(cls, v):
        headings = [s.heading for s in v]
        if len(headings) != len(set(headings)):
            raise ValueError("Duplicate section headings are not allowed")
        return v


# ── Doc-type Outline Validation (Template Compliance) ─────────────────────────

REQUIRED_OUTLINE_KEYWORDS = {
    "Proposal": ["scope", "objectives", "deliverables", "timeline", "risks"],
    "Technical Report": ["background", "implementation", "risks", "recommendations"],
    "Executive Summary": ["scope", "insights", "recommendations"],
    "Policy Brief": ["issue", "options", "recommendation", "implementation"],
    "Invoice": ["line", "total", "payment"],
    "Letter": ["greeting", "closing", "signature"],
    "Solution Overview": ["problem", "solution", "benefits", "next"],
    "Meeting Brief": ["agenda", "decisions", "action"],
}

def validate_outline_for_doc_type(outline: "OutlineResponse", doc_type: str) -> None:
    req = REQUIRED_OUTLINE_KEYWORDS.get(doc_type)
    if not req:
        return

    # Check headings + descriptions (robust)
    text = " ".join([(s.heading + " " + s.description).lower() for s in outline.sections])
    missing = [k for k in req if k not in text]
    if missing:
        raise ValueError(f"Outline missing required elements for {doc_type}: {', '.join(missing)}")


# ── Section Writer Schemas ───────────────────────────────────────────────────

class SectionWriterResponse(BaseModel):
    section_body: str = Field(..., min_length=10, description="Markdown body text with inline citations")

    # Allow empty citations in model_only
    citations_used: List[str] = Field(
        default_factory=list,
        description="List of cite_ids actually referenced"
    )

    conflict_detected: bool = Field(default=False, description="True if the uploaded documents have a direct factual contradiction")
    conflict_description: Optional[str] = Field(default=None, description="Detailed explanation of the conflicting facts (if any)")

    missing_info: Optional[str] = Field(default=None, description="Description of missing information, if any")
    followup_question: Optional[str] = Field(default=None, description="Clarification question if evidence was insufficient")



# ── Template Generator Schemas ────────────────────────────────────────────────

class TemplateSection(BaseModel):
    title: str
    bullets: List[str]
    actual_content_preview: List[str] = Field(default_factory=list, description="2-3 specific content snippets or expected insights for this section")

class TemplateGeneratorResponse(BaseModel):
    doc_type: str = Field(..., min_length=3)
    metadata: Dict[str, str] = Field(default_factory=dict)
    structure: Dict[str, TemplateSection] = Field(
        ..., 
        description="Mapping of section_name to TemplateSection(title, bullets)"
    )


# ── Parsing Helpers ──────────────────────────────────────────────────────────

def _clean_json_string(raw: str) -> str:
    """Strip common LLM wrapper artefacts (markdown fences, trailing text)."""
    text = raw.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        text = text[first_newline + 1:] if first_newline != -1 else text[3:]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def parse_and_validate_outline(raw_json: str) -> OutlineResponse:
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return OutlineResponse.model_validate(data)


def parse_and_validate_section(raw_json: str) -> SectionWriterResponse:
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return SectionWriterResponse.model_validate(data)


def parse_and_validate_template(raw_json: str) -> TemplateGeneratorResponse:
    cleaned = _clean_json_string(raw_json)
    data = json.loads(cleaned)
    return TemplateGeneratorResponse.model_validate(data)