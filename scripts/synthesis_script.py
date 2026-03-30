import os
import json
import uuid
import yaml
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv

# Ensure we use the existing OpenAI setup
from src.generation.llm import call_llm

load_dotenv()

SYNTHESIS_PROMPT = """You are an expert Data Engineer preparing a dataset for fine-tuning an AI writer.
Your job is to reverse-engineer this official government document into "Training Pairs".

For the provided text chunk, extract 1 to 3 logical sections.
For each section, you must create:
1) An "Evidence Pack" (the raw facts stripped of their elegant writing).
2) The "Golden Output" (the EXACT original text from the document, perfectly preserved).

== RULES ==
- The `golden_output` must be the EXACT text from the document. Do not summarize or rewrite it. This is what we want the AI to learn to write.
- The `evidence_pack` must be raw, bulleted facts separated by citations like "[S1]", "[S2]".
- If the chunk is just a title page or table of contents, return an empty sections list.
- Keep the language in ARABIC.

== INPUT CHUNK ==
{chunk}

== OUTPUT FORMAT (JSON ONLY) ==
{{
    "sections": [
        {{
            "topic": "Name of the broader document/topic",
            "heading": "Heading of this specific section",
            "evidence_pack": "[S1] Fact one. [S2] Fact two...",
            "golden_output": "(The exact original Arabic text corresponding to those facts)"
        }}
    ]
}}
"""

def extract_text_from_pdf(pdf_path: str) -> list[str]:
    reader = PdfReader(pdf_path)
    # Group pages into chunks of 2 to ensure enough context for a section
    chunks = []
    current_chunk = ""
    for i, page in enumerate(reader.pages):
        current_chunk += page.extract_text() + "\n"
        if (i + 1) % 2 == 0 or i == len(reader.pages) - 1:
            chunks.append(current_chunk)
            current_chunk = ""
    return chunks

def synthesize_pairs(pdf_path: str, output_jsonl: str):
    print(f"📄 Processing document: {pdf_path}")
    chunks = extract_text_from_pdf(pdf_path)
    
    pairs_generated = 0
    with open(output_jsonl, 'a', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            print(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
            prompt = SYNTHESIS_PROMPT.format(chunk=chunk[:4000]) # Safe context limit
            
            messages = [
                {"role": "system", "content": "You are a data synthesis engine. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = call_llm(messages, json_mode=True)
                data = json.loads(response)
                
                for section in data.get("sections", []):
                    # Format as required for fine-tuning (e.g., Llama-3 Instruct format)
                    system_message = "You are an official Government Technical Writer. Write the section based on the evidence."
                    user_message = f"Topic: {section['topic']}\nHeading: {section['heading']}\nEvidence:\n{section['evidence_pack']}"
                    
                    training_row = {
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message},
                            {"role": "assistant", "content": section['golden_output']}
                        ]
                    }
                    
                    f.write(json.dumps(training_row, ensure_ascii=False) + "\n")
                    pairs_generated += 1
            except Exception as e:
                print(f"⚠️ Failed to parse chunk {i+1}: {e}")
                
    print(f"✅ Synthesis complete. Generated {pairs_generated} golden pairs in {output_jsonl}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate fine-tuning data from official PDFs.")
    parser.add_argument("pdf_path", help="Path to the source PDF document.")
    parser.add_argument("--output", default="training_data.jsonl", help="Output JSONL file.")
    
    args = parser.parse_args()
    synthesize_pairs(args.pdf_path, args.output)
