import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_model(tier: str = "small", temperature: float = 0):
    """
    Tiered model selection for cost control.
    Small: gpt-4o-mini (Planning/Reasoning)
    Large: gpt-4o (Generation/Synthesis)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    
    model_name = "gpt-4o-mini" if tier == "small" else "gpt-4o"
    
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )

def call_llm(messages: List[Dict[str, Any]], json_mode: bool = False) -> str:
    """
    Unified LLM call wrapper with JSON mode support.
    """
    # Use small model for structure/JSON, large for final generation
    tier = "small" if json_mode else "large"
    model = get_model(tier=tier)
    
    if json_mode:
        model = model.bind(response_format={"type": "json_object"})
        # Safety: Ensure "json" is in the messages to satisfy OpenAI requirements
        has_json = any("json" in (m.get("content", "").lower() if isinstance(m, dict) else getattr(m, "content", "").lower()) for m in messages)
        if not has_json:
            if isinstance(messages[-1], dict):
                messages[-1]["content"] += " (Respond in valid JSON format)"
            else:
                # If they are LangChain message objects
                messages[-1].content += " (Respond in valid JSON format)"
        
    response = model.invoke(messages)
    return str(response.content)
