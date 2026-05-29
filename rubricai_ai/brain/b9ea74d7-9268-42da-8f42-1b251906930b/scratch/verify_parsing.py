import sys
import os
import re
from pathlib import Path

# Add the parent directory to sys.path so we can import modules
parent_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(parent_dir))

try:
    from rag.utils import get_instrument_list
    print("Testing get_instrument_list()...")
    
    # We need to ensure the path in get_instrument_list exists in this environment
    md_path = parent_dir / "rag" / "documentos_maestros" / "instrumentos_de_evaluacion.md"
    
    if md_path.exists():
        content = md_path.read_text(encoding="utf-8")
        matches = list(re.finditer(r"^\*\*(.*?)\*\*[:\s]*(.*?)$", content, re.MULTILINE))
        print(f"Found {len(matches)} instruments.")
        for m in matches[:3]:
            print(f"- {m.group(1).strip()}")
        
        if len(matches) > 0:
            print("Regex Success!")
        else:
            print("Regex Failure!")
    else:
        print(f"File not found: {md_path}")

except Exception as e:
    print(f"Error during verification: {e}")
