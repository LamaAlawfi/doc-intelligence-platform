import os
import sys
import uuid
import json
from src.graph.builder import build_graph

def run_main():
    print("🏛️ GOVERNMENT DOCUMENT INTELLIGENCE - TERMINAL MODE")
    print("-" * 50)
    
    # 1. Initialize Graph
    graph = build_graph()
    
    # 2. Setup initial state
    # Example: Document Planner mission
    state = {
        "files": [],
        "logs": [],
        "status": "idle",
        "language": "EN",
        "user_answers": {
            "purpose": "National AI Safety Framework",
            "template_mode": "Executive Summary Mode",
            "task_mode": "template_gen"
        }
    }
    
    print(f"🚀 Mission: Generating structure for '{state['user_answers']['purpose']}'")
    print("⏳ Agent is architecting... (Deep Synthesis Active)")
    
    # 3. Invoke Graph
    try:
        final_state = graph.invoke(state)
        
        # 4. Show Output
        template = final_state.get("generated_template")
        if template:
            print("\n✅ SUCCESS: Document Architecture Generated")
            print("-" * 50)
            print(f"Type: {template.get('doc_type')}")
            print(f"Classification: {template.get('metadata', {}).get('classification')}")
            print("\nProposed Sections:")
            for k, v in template.get("structure", {}).items():
                print(f"  - {v.get('title')}")
            
            print("-" * 50)
            print(f"Logs: {len(final_state.get('logs', []))} operations performed.")
        else:
            print("\n❌ Error: No structure was generated.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL SYSTEM ERROR: {str(e)}")

if __name__ == "__main__":
    run_main()
