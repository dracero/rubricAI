import os
import faiss
import pickle
from rag.embed import embed_texts
from rag.store import get_index_path, get_metadata_path

def index_directrices():
    """
    Lee el archivo directrices.md, lo divide en fragmentos lógicos
    (por secciones) y lo indexa asociado al course_id = 0.
    """
    path = os.path.join(os.path.dirname(__file__), "directrices.md")
    if not os.path.exists(path):
        print(f"Error: No se encontró {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Dividir el documento por encabezados principales o tablas (simplificado)
    # Como es un markdown estructurado, podemos hacer un split básico pero útil
    import re
    # Separamos basándonos en dobles saltos de línea largos o secciones grandes
    paragraphs = re.split(r'\n\s*\n', content)
    
    chunks = []
    current_chunk = []
    current_length = 0
    # Agrupamos párrafos hasta un límite razonable (ej. 1000 caracteres)
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Tratar de mantener un contexto temático por "chunk"
        if len(p) > 2000: # Si es una tabla gigante o párrafo enorme, lo partimos
            subchunks = [p[i:i+1500] for i in range(0, len(p), 1500)]
            for sc in subchunks:
                chunks.append(sc)
            continue
            
        if current_length + len(p) > 1500 and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [p]
            current_length = len(p)
        else:
            current_chunk.append(p)
            current_length += len(p)
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    print(f"Dividido en {len(chunks)} fragmentos.")

    metadata = []
    
    # Prefix chunks to help E5 model
    from rag.utils import embed_text_chunks
    embeddings = embed_text_chunks(chunks, prefix="passage: ")
    
    for i, chunk in enumerate(chunks):
        metadata.append({
            "course_id": 0,
            "filename": "directrices.md",
            "page": 1,
            "text": chunk
        })

    # Guardar en Faiss para course_id = 0
    from rag.store import save_index
    save_index(0, embeddings, metadata)
    print("Directrices indexadas correctamente en course_id=0.")

if __name__ == "__main__":
    index_directrices()
