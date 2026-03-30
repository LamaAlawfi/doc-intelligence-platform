import os
import uuid
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph.builder import build_graph
from src.ingest.readers import read_file

load_dotenv()

def main():
    print("\n" + "="*50)
    print("      📄 DOCUMENT AGENT: QUICK vs GUIDED")
    print("="*50)
    
    # 0. Ingestion
    print("\n[Stage 0: Ingestion]")
    raw_input = input("Enter file paths (comma separated): ")
    file_paths = [p.strip() for p in raw_input.split(",") if p.strip()]
    
    files = []
    for path in file_paths:
        if os.path.exists(path):
            try:
                text, meta = read_file(path)
                files.append({
                    "id": str(uuid.uuid4()),
                    "name": os.path.basename(path),
                    "type": os.path.splitext(path)[1],
                    "text": text,
                    "meta": meta
                })
                print(f"✅ Loaded: {os.path.basename(path)}")
            except Exception as e:
                print(f"❌ Error loading {path}: {e}")
    
    if not files:
        print("No valid files loaded. Exiting.")
        return

    graph = build_graph()
    state = {"files": files, "logs": [], "status": "start", "warnings": [], "errors": [], "mode": "quick"}
    
    # Run Ingestion & Suggestions
    print("\n[Process] Analyzing Documents & Generating Suggestions ...")
    state = graph.invoke(state)
    
    if state.get("errors"):
        print("\nHALTED: " + state["errors"][0])
        return

    # Mode Selection
    print("\n" + "-"*30)
    print("  CHOOSE YOUR PATH")
    print("  [1] Quick Generate (Recommended)")
    print("  [2] Guided Mode (Full Control)")
    print("-"*30)
    mode_choice = input("Choice [1]: ") or "1"
    state["mode"] = "quick" if mode_choice == "1" else "guided"

    # Suggestions Panel (CLI)
    sug = state.get("suggestions", {})
    if sug:
        print("\n💡 SMART SUGGESTIONS:")
        print(f"   Detected Themes: {', '.join(sug['topics'])}")
        print(f"   Recommended: {list(sug['templates'].keys())[0]}")
        # Removed file-name leakage from Primary Suggestion

    # 1. Questionnaire / Fast-Track
    print("\n" + "-"*30)
    print(f"  STAGE 1: STRATEGY ({state['mode'].upper()})")
    print("-"*30)
    
    answers = {}
    formats = ["Markdown", "PDF", "DOCX", "TXT"]
    
    if state["mode"] == "quick":
        # QUICK MODE PROMPTS
        print("\nQ3) Output doc type? (e.g. Proposal, Technical Report)")
        default_type = list(sug['templates'].keys())[0] if sug else "Proposal"
        answers["doc_type"] = input(f"[{default_type}]: ") or default_type
        
        print("\nQ1) Primary Source(s)? (Numbers, comma separated)")
        for idx, f in enumerate(files):
            is_suggested = " [SUGGESTED]" if sug and f["id"] in sug.get("primary_file_ids", []) else ""
            print(f"  {idx+1}) {f['name']}{is_suggested}")
        choice = input("> ")
        if not choice.strip():
            answers["primary_files"] = sug.get("primary_file_ids", []) if sug else [files[0]["id"]]
        else:
            answers["primary_files"] = [files[int(i)-1]["id"] for i in choice.split(",") if i.strip()]
            
        print("\nQ) Output format?")
        for idx, fmt in enumerate(formats): print(f"  [{idx+1}] {fmt}")
        try:
            fmt_choice = input(f"Choice [1-{len(formats)}]: ") or "1"
            answers["output_format"] = formats[int(fmt_choice)-1]
        except (ValueError, IndexError):
            print("  ⚠️ Invalid choice. Defaulting to Markdown.")
            answers["output_format"] = "Markdown"
        
        print("\nQ6) Main purpose?")
        print(f"  Suggested: {sug['purposes'][0] if sug else 'Synthesize documents'}")
        answers["purpose"] = input("> ") or (sug['purposes'][0] if sug else "Synthesize documents")
        
        # Defaults for Quick Mode
        answers["scope_mode"] = "3) Combine all docs"
        answers["audience"] = "General"
        answers["tone"] = "Formal"
        answers["must_include"] = ""
        answers["must_avoid"] = ""
        answers["length"] = "1 page"
        
    else:
        # GUIDED MODE PROMPTS (Full set)
        print("\nQ1) Primary Source(s)? (Numbers, comma separated)")
        for idx, f in enumerate(files): print(f"  {idx+1}) {f['name']}")
        choice = input("> ")
        answers["primary_files"] = [files[int(i)-1]["id"] for i in choice.split(",") if i.strip()]
        
        print("\nQ2) Reference Template File (Number, or empty for none)?")
        ref_choice = input("> ")
        if ref_choice.strip() and ref_choice.strip().isdigit() and int(ref_choice)-1 < len(files):
            state["ref_template_id"] = files[int(ref_choice)-1]["id"]

        answers["scope_mode"] = input("\nQ2) Scope mode (1: 1-doc, 2: Merge, 3: All, 4: Synthesize)? > ")
        answers["doc_type"] = input("\nQ3) Doc type? > ")
        
        print("\nQ10) Output format?")
        for idx, fmt in enumerate(formats): print(f"  [{idx+1}] {fmt}")
        try:
            fmt_choice = input(f"Choice [1-{len(formats)}]: ") or "1"
            answers["output_format"] = formats[int(fmt_choice)-1]
        except (ValueError, IndexError):
            print("  ⚠️ Invalid choice. Defaulting to Markdown.")
            answers["output_format"] = "Markdown"
        
        answers["audience"] = input("\nQ4) Audience [General]? > ") or "General"
        answers["tone"] = input("\nQ5) Tone [Formal]? > ") or "Formal"
        answers["purpose"] = input("\nQ6) Purpose? > ")
        answers["must_include"] = input("\nQ7) Must-include? > ")
        answers["must_avoid"] = input("\nQ8) Must-avoid? > ")
        answers["length"] = input("\nQ9) Length [1 page]? > ") or "1 page"

    # Resume Pipeline
    print("\n" + "-"*30)
    print("  EXECUTING PLANNING STAGE")
    print("-"*30)
    
    state["user_answers"] = answers
    state["status"] = "awaiting_answers"
    state = graph.invoke(state)
    
    # 2. Outline Preview (CLI Version)
    if state.get("status") == "awaiting_outline_approval":
        print("\n" + "="*50)
        print("      STAGE 2: OUTLINE PREVIEW")
        print("="*50)
        outline = state.get("outline", [])
        import json
        print(json.dumps(outline, indent=2))
        
        print("\n[Action Required] Approve this structure?")
        print("  [1] Yes, start generation")
        print("  [2] No, I want to edit (JSON)")
        print("  [3] Terminate")
        
        preview_choice = input("Choice [1]: ") or "1"
        
        if preview_choice == "2":
            print("\nEnter new JSON outline (Press Ctrl+D/Ctrl+Z when finished):")
            try:
                raw_json = sys.stdin.read()
                state["outline"] = json.loads(raw_json)
            except Exception as e:
                print(f"❌ Invalid JSON. Proceeding with original. Error: {e}")
        elif preview_choice == "3":
            print("Halted by user.")
            return

        print("\n[Process] Executing strictly grounded RAG pipeline ...")
        state["status"] = "outline_approved"
        state = graph.invoke(state)
    
    # Final Report
    if state.get("warnings"):
        print("\n⚠️ WARNINGS:")
        for w in state["warnings"]: print(f"  - {w}")
        
    if state.get("output_path"):
        print(f"\n✅ SUCCESS: Document generated.")
        print(f"📍 Path: {state['output_path']}")
    else:
        print("\n❌ Pipeline failed.")
        if state.get("errors"):
            for err in state["errors"]: print(f"  - {err}")

    print("\n" + "="*50)

if __name__ == "__main__":
    main()
