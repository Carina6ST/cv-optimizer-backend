# backend/services/ai.py
import os
from typing import Dict
from core.config import settings

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _client():
    if settings.AI_PROVIDER != "openai":
        return None
    if not settings.OPENAI_API_KEY or OpenAI is None:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_SUGGEST = """You are an ATS-savvy CV optimization assistant.
- Analyze the candidate CV against the job description.
- Give precise, up-to-date guidance: missing hard skills/tools, certifications, phrasing that ATS favors.
- Prefer short, actionable bullets. Use UK/US spelling neutral language.
- Do NOT hallucinate experience; if missing, suggest learning/wording alternatives.
Return JSON with: 'summary', 'missing_skills', 'phrasing_tips', 'section_level_tweaks'."""

SYSTEM_REWRITE = """You are an expert CV editor producing ATS-friendly rewrites.
- Rewrite the candidate's CV to align with the job description.
- Preserve truth; never invent roles, dates, or employers.
- Optimize for keyword coverage and clarity, use strong action verbs, quantify impact when possible.
- Keep the structure: Summary, Experience (bullets), Skills, Education, Certifications.
- Output plain text only, ready to paste into a DOCX.
"""

def ai_suggestions(cv_text: str, jd_text: str) -> Dict:
    if settings.AI_PROVIDER != "openai" or not settings.OPENAI_API_KEY or OpenAI is None:
        # Mock: simple deterministic placeholder
        return {
            "summary": "Focus on aligning your technical stack and outcomes with the JD.",
            "missing_skills": ["docker", "kubernetes"] if "docker" in jd_text.lower() else [],
            "phrasing_tips": [
                "Use action verbs (led, implemented, optimized) and quantify results.",
                "Mirror exact JD terminology where accurate."
            ],
            "section_level_tweaks": {
                "Summary": "Mention role title from JD and 2–3 matching core skills.",
                "Skills": "Group tools by category; put required ones first.",
            }
        }
    client = _client()
    prompt = f"JOB DESCRIPTION:\n{jd_text}\n\nCANDIDATE CV:\n{cv_text}\n"
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":SYSTEM_SUGGEST},{"role":"user","content":prompt}],
        temperature=0.2,
    )
    import json
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        # fallback if model didn’t return strict JSON
        return {"summary": resp.choices[0].message.content}

def ai_rewrite(cv_text: str, jd_text: str) -> str:
    if settings.AI_PROVIDER != "openai" or not settings.OPENAI_API_KEY or OpenAI is None:
        return ("[Mock rewrite]\n"
                "• Align your headline with the JD title.\n"
                "• Front-load required tools/skills.\n"
                "• Add quantified impact in bullets.")
    client = _client()
    prompt = f"JOB DESCRIPTION:\n{jd_text}\n\nORIGINAL CV:\n{cv_text}\n"
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role":"system","content":SYSTEM_REWRITE},{"role":"user","content":prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
