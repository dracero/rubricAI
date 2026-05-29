import os
from pypdf import PdfReader
from docx import Document

CHUNK_SIZE = 800
OVERLAP = 150


def extract_text(filepath):
    try:
        if filepath.endswith(".pdf"):
            reader = PdfReader(filepath)
            return "\n".join([p.extract_text() or "" for p in reader.pages])

        elif filepath.endswith(".docx"):
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])

        elif filepath.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    except Exception:
        return ""

    return ""


def chunk_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - OVERLAP

    return chunks
