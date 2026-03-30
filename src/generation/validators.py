"""
Post-generation validators — no LLM calls.
1. Citation Validator: checks that every paragraph has citations and all cite_ids are real.
2. Coverage Validator: checks that every primary source appears in intro + >=1 body section.
"""
import re
from typing import Dict, List, Tuple, Any, Set


# ── Citation Validator ───────────────────────────────────────────────────────

def validate_citations(
    section_body: str,
    citations_used: List[str],
    chunk_index: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Validates citations in a single section.

    Args:
        section_body:    The rendered markdown text of the section.
        citations_used:  List of cite_ids the writer claims it used
                         (e.g. ["S1:fileA_C003", "S2:fileB_C010"]).
        chunk_index:     Mapping of *raw* chunk_id -> chunk data
                         (keys like "fileA_C003", without the S-prefix).

    Returns:
        (is_valid, issues)  where issues is an empty list if valid.
    """
    issues: List[str] = []

    # 1. Every cite_id in citations_used must point to a real chunk
    for cite_id in citations_used:
        # cite_id format is "S1:fileA_C003"  →  raw chunk_id = "fileA_C003"
        raw_id = cite_id.split(":", 1)[-1] if ":" in cite_id else cite_id
        if raw_id not in chunk_index:
            issues.append(f"Phantom citation: {cite_id} does not exist in chunk index")

    # 2. Every paragraph must include at least one citation marker [...]
    paragraphs = [p.strip() for p in section_body.split("\n\n") if p.strip()]
    for i, para in enumerate(paragraphs):
        # Match patterns like [S1:fileA_C003] or [fileA_C003]
        markers = re.findall(r'\[[A-Za-z0-9_:\-]+\]', para)
        if not markers:
            issues.append(f"Paragraph {i + 1} contains no citation markers")

    is_valid = len(issues) == 0
    return is_valid, issues


# ── Coverage Validator ───────────────────────────────────────────────────────

def validate_coverage(
    retrieval_map: Dict[str, Dict[str, Any]],
    primary_files: List[str],
    file_id_to_src: Dict[str, str],
    outline: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Checks that every primary source is represented via chunk IDs
    in the Introduction AND at least one body section.

    Args:
        retrieval_map:   heading -> {"evidence": [...], "context_string": "..."}
        primary_files:   List of real file IDs that must be covered.
        file_id_to_src:  file_id -> "source_X" mapping (for logging).
        outline:         List of section dicts (first = intro, rest = body).

    Returns:
        (is_valid, missing_source_labels)
    """
    if not primary_files or not outline:
        return True, []

    # Sources present in intro
    intro_heading = outline[0]["heading"]
    intro_evidence = retrieval_map.get(intro_heading, {}).get("evidence", [])
    intro_sources: Set[str] = {c["file_id"] for c in intro_evidence}

    # Sources present in any body section
    body_sources: Set[str] = set()
    for section in outline[1:]:
        evidence = retrieval_map.get(section["heading"], {}).get("evidence", [])
        for c in evidence:
            body_sources.add(c["file_id"])

    missing = []
    for fid in primary_files:
        src_label = file_id_to_src.get(fid, fid)
        if fid not in intro_sources:
            missing.append(f"{src_label} missing from Introduction")
        if fid not in body_sources:
            missing.append(f"{src_label} missing from all body sections")

    return len(missing) == 0, missing
