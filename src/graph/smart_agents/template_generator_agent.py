import os
import logging
from typing import Dict, Any

from src.generation.prompts import generate_template

logger = logging.getLogger(__name__)

def template_generator_agent(
    topic: str, 
    mode: str = "Executive Summary Mode", 
    model: str = "gpt-4o-mini",
    language: str = "Arabic",
    bilingual_intro_concl: bool = False
) -> Dict[str, Any]:
    """
    Agent that generates a standardized JSON template structure based on a topic and mode.
    """
    logger.info(f"Generating template for topic: {topic} (Mode: {mode}, Lang: {language})")
    
    try:
        # We pass the topic and mode to the generate_template function
        template_response = generate_template(topic, mode, language=language, bilingual_intro_concl=bilingual_intro_concl)
        
        # Return the model_dump which including 'doc_type', 'metadata', and 'structure'
        return template_response.model_dump()
        
    except Exception as e:
        logger.error(f"Template Generator Agent failed: {str(e)}")
        # Return a safe fallback structure
        return {
            "doc_type": f"Official Template: {topic}",
            "metadata": {
                "classification": "INTERNAL",
                "version": "1.0",
                "owner_dept": "General"
            },
            "structure": {
                "executive_summary": {"title": "Executive Summary", "bullets": [1, 2, 3]},
                "background": {"title": "Background / Regulatory Context", "bullets": [1, 2, 3]},
                "objectives": {"title": "Strategic Objectives", "bullets": [1, 2, 3]},
                "conclusion": {"title": "Conclusion & Approval", "bullets": [1, 2, 3]}
            }
        }
