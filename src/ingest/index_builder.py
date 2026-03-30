import re
from typing import List, Dict, Any
from collections import Counter

def build_heuristic_index(file_id: str, name: str, text: str) -> Dict[str, Any]:
    # 1. Length estimate (approx tokens or words)
    words = re.findall(r'\w+', text.lower())
    length = len(words)
    
    # 2. Key keywords (simple frequency-based filters)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'in', 'of', 'for', 'with', 'on', 'at', 'by', 'from', 'this', 'that', 'with'}
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    top_keywords = [k for k, v in Counter(keywords).most_common(10)]
    
    # 3. Quick preview (increased to ~10 sentences / 1500 chars)
    sentences = re.split(r'(?<=[.!?]) +', text[:2000])
    preview = " ".join(sentences[:10]).strip()
    if len(preview) > 1500:
        preview = preview[:1500] + "..."
    else:
        preview += "..."
    
    return {
        "file_id": file_id,
        "name": name,
        "length": length,
        "keywords": top_keywords,
        "preview": preview
    }
def chunk_text(file_id: str, file_name: str, text: str, chunk_size: int = 400, overlap: int = 80) -> List[Dict[str, Any]]:
    """
    Standardized word-based chunking.
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = " ".join(chunk_words)
        
        if len(chunk_words) < 50 and len(chunks) > 0:
            chunks[-1]["text"] += " " + chunk_text
            chunks[-1]["meta"]["end_word"] = i + len(chunk_words)
            continue
            
        chunk_id = f"{file_id}_C{len(chunks):03d}"
        chunks.append({
            "file_id": file_id,
            "file_name": file_name,
            "text": chunk_text,
            "chunk_id": chunk_id,
            "chunk_idx": len(chunks),
            "meta": {
                "start_word": i,
                "end_word": i + len(chunk_words)
            }
        })
        
    return chunks
