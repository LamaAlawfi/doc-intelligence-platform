from typing import TypedDict, List, Dict, Any, Optional

class FileItem(TypedDict):
    id: str
    name: str
    type: str
    text: str
    meta: Dict[str, Any]

class FileIndexItem(TypedDict):
    file_id: str
    name: str
    length: int
    keywords: List[str]
    preview: str

class DocAgentState(TypedDict):
    # Stage 0: Ingestion
    files: List[FileItem]
    file_index: List[FileIndexItem]
    
    # Stage 1: Questionnaire
    user_answers: Dict[str, Any]
    doc_spec: Dict[str, Any]
    
    # Stage 2: Planning
    outline: List[Dict[str, Any]]
    
    # Stage 3: Retrieval
    chunks: List[Dict[str, Any]]
    retrieval_map: Dict[str, List[Dict[str, Any]]] # section_id -> chunks
    
    # Stage 4: Generation
    draft_sections: Dict[str, str] # section_id -> content
    final_doc: Optional[str]
    
    # Mode & Suggestions
    mode: str # "quick" or "guided"
    suggestions: Dict[str, Any]
    
    # Engine (Instance reuse)
    retrieval_engine: Optional[Any]
    
    # Source mapping (anonymized labels)
    file_id_to_src: Dict[str, str]  # file_id -> "source_1", "source_2", etc.
    
    # Post-generation validation
    validation_results: Dict[str, Any]  # citation + coverage results
    
    # Self-healing tracking
    retry_counts: Dict[str, int]  # node_name -> count

    # Template Reference
    ref_template_id: Optional[str]  # ID of the document to use as structure/style ref
    generated_template: Optional[Dict[str, Any]] # NEW: Result from Template Generator
    
    # Status & Logistics
    current_step: int
    final_doc_title: Optional[str]   # NEW: Title of the generated document
    output_path: Optional[str]
    status: str
    warnings: List[str]
    errors: List[str]
    logs: List[Dict[str, Any]]
