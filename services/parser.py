import os
from typing import Optional
import pdfplumber
from docx import Document

def extract_text(path: str) -> Optional[str]:
    _, ext = os.path.splitext(path.lower())
    try:
        if ext == ".pdf":
            return _pdf_text(path)
        elif ext == ".docx":
            return _docx_text(path)
    except Exception:
        return None
    return None

def _pdf_text(path: str) -> str:
    chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)

def _docx_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)
