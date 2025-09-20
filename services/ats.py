import re
from typing import Tuple, List, Dict
import textstat

def tokenize(s: str) -> List[str]:
    return re.findall(r"[a-zA-Z]+", s.lower())

def find_keywords(resume_text: str, job_description: str) -> Tuple[list[str], list[str]]:
    if not job_description:
        return [], []
    r_toks = set(tokenize(resume_text))
    j_toks = set(tokenize(job_description))
    matched = sorted(list(r_toks & j_toks))
    missing = sorted(list(j_toks - r_toks))[:50]
    return matched, missing

def readability(text: str) -> Dict:
    if not text.strip():
        return {"flesch": 0, "grade_level": 0, "label": "Unknown"}
    flesch = textstat.flesch_reading_ease(text)
    grade = textstat.text_standard(text, float_output=True)
    label = "Easy" if flesch >= 60 else "Medium" if flesch >= 30 else "Hard"
    return {"flesch": round(flesch, 2), "grade_level": round(grade, 1), "label": label}

def ats_check(text: str) -> Dict:
    issues = {
        "tables": 0,
        "images": 0,
        "multi_column_lines": 1 if "  " in text else 0,
        "non_standard_fonts": 0
    }
    score = max(40, 100 - (issues["multi_column_lines"] * 5))
    return {
        "ats_friendly_score": f"{score}%",
        "issues_found": issues,
        "summary": "Use single-column layout; avoid images/tables; keep standard fonts."
    }
