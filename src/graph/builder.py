from langgraph.graph import StateGraph, END
from src.graph.state import DocAgentState
from src.graph.nodes import (
    node_router,
    node_load_files,
    node_build_file_index,
    node_token_guard,
    node_questionnaire_builder,
    node_normalize_doc_spec,
    node_planning, # RENAMED
    node_chunk_docs,
    node_retrieve_evidence,
    node_coverage_checker,
    node_section_writer,
    node_citation_validator,
    node_conflict_resolver,
    node_assemble_document,
    node_traceability_appendix,
    node_missing_elements_detector,
    node_export_document,
    node_chat_qa,
    node_template_generator,
    node_groundedness_validator,
    node_quality_checker, # NEW
)

def build_graph():
    g = StateGraph(DocAgentState)

    # Ingestion / Index
    g.add_node("load", node_load_files)
    g.add_node("index", node_build_file_index)
    g.add_node("token_guard", node_token_guard)

    # Questionnaire + Spec
    g.add_node("questionnaire", node_questionnaire_builder)
    g.add_node("normalization", node_normalize_doc_spec)

    # Planning
    g.add_node("planning", node_planning)

    # Retrieval + Generation
    g.add_node("chunking", node_chunk_docs)
    g.add_node("retrieval", node_retrieve_evidence)
    g.add_node("coverage", node_coverage_checker)
    g.add_node("generation", node_section_writer)
    g.add_node("citation_validation", node_citation_validator)
    g.add_node("conflict", node_conflict_resolver)
    g.add_node("assembly", node_assemble_document)
    g.add_node("traceability", node_traceability_appendix)
    g.add_node("missing_elements", node_missing_elements_detector)
    g.add_node("quality_check", node_quality_checker) # NEW
    g.add_node("groundedness_check", node_groundedness_validator)
    g.add_node("export", node_export_document)

    # Chat
    g.add_node("chat", node_chat_qa)
    
    # Template Generation
    g.add_node("template_generator", node_template_generator)

    # Entry
    g.set_entry_point("load")

    # Main linear flow (until planning)
    g.add_edge("load", "index")
    g.add_edge("index", "token_guard")

    # Router (based on status/spec)
    g.add_conditional_edges("token_guard", node_router, {
        "questionnaire": "questionnaire",
        "normalization": "normalization",
        "planning": "planning",
        "template_generator": "template_generator", # NEW
        "stop": END,
    })

    g.add_edge("questionnaire", END)
    
    def post_normalization_router(state: DocAgentState) -> str:
        if state.get("doc_spec", {}).get("task_mode") == "template_gen":
            return "template_generator"
        return "planning"

    g.add_conditional_edges("normalization", post_normalization_router, {
        "template_generator": "template_generator",
        "planning": "planning"
    })

    # After planning: if task_mode == chat -> go chat, else stop at outline approval
    def after_planning_router(state: DocAgentState) -> str:
        status = state.get("status")
        if status == "outline_approved":
            return "chunking"
            
        spec = state.get("doc_spec", {})
        task_mode = spec.get("task_mode", "generate_document")
        if task_mode == "chat":
            return "chat"
        return "stop"

    g.add_conditional_edges("planning", after_planning_router, {
        "chat": "chat",
        "chunking": "chunking",
        "stop": END,
    })

    # Template Gen ends
    g.add_edge("template_generator", END)

    # Chat ends
    g.add_edge("chat", END)

    # The rest of the doc pipeline runs only after outline is approved (UI triggers graph again)
    g.add_edge("chunking", "retrieval")
    g.add_edge("retrieval", "coverage")
    g.add_edge("coverage", "generation")
    g.add_edge("generation", "citation_validation")
    g.add_edge("citation_validation", "conflict")
    g.add_edge("conflict", "assembly")
    g.add_edge("assembly", "traceability")
    g.add_edge("traceability", "missing_elements")
    g.add_edge("missing_elements", "quality_check")
    g.add_edge("quality_check", "groundedness_check")
    g.add_edge("groundedness_check", "export")
    g.add_edge("export", END)

    return g.compile()
