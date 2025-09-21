# backend/services/ai.py
import os
from typing import Dict, Any

from core.config import settings

# Optional tiktoken import (graceful fallback if not installed)
def _count_tokens(text: str) -> int:
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text or ""))
    except Exception:
        # Lightweight fallback: ~1 token ~= 0.75 words
        return max(1, int(len((text or "").split()) / 0.75))

def ai_suggestions(cv_text: str, job_description: str) -> Dict[str, Any]:
    provider = (settings.AI_PROVIDER or "mock").lower()

    if provider == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            system = (
                "You are an ATS and career expert. "
                "Analyze the candidate CV against the job description, "
                "return structured suggestions to improve ATS score, "
                "keyword alignment, clarity, impact, and formatting. "
                "Keep it concise and actionable."
            )
            user = (
                f"JOB DESCRIPTION:\n{job_description}\n\n"
                f"CV TEXT:\n{cv_text}\n\n"
                "Return JSON with keys: score (0-100), missing_keywords[], strengths[], issues[], suggestions[]"
            )

            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-4o-mini",
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.2,
            )

            content = resp.choices[0].message.content or ""
            return {
                "model": settings.OPENAI_MODEL or "gpt-4o-mini",
                "raw": content,
                "tokens_estimate": _count_tokens(cv_text + "\n" + job_description),
            }
        except Exception as e:
            # Fallback to mock if OpenAI fails
            return {
                "model": "mock",
                "raw": f"[openai_error:{e}] Falling back to heuristic suggestions.",
                "tokens_estimate": _count_tokens(cv_text + "\n" + job_description),
            }

    # Mock provider (default)
    from services.ats import extract_keywords
    jd_kw = extract_keywords(job_description)
    cv_kw = extract_keywords(cv_text)
    missing = [k for k in jd_kw if k.lower() not in (kw.lower() for kw in cv_kw)]
    score = max(10, 100 - 2 * len(missing))

    return {
        "model": "mock",
        "raw": "Heuristic ATS suggestions (no external model).",
        "score": score,
        "missing_keywords": missing[:25],
        "suggestions": [
            "Add more role-specific keywords from the JD into your Experience bullets.",
            "Quantify achievements (numbers, %, $) to improve impact.",
            "Use standard headings: Summary, Experience, Education, Skills.",
            "Keep format simple (PDF, one column) for ATS parsing.",
        ],
        "tokens_estimate": _count_tokens(cv_text + "\n" + job_description),
    }

def ai_rewrite(cv_text: str, job_description: str) -> str:
    provider = (settings.AI_PROVIDER or "mock").lower()

    if provider == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            system = (
                "You rewrite CV content to align with a given job description "
                "without fabricating experience. Keep original truth, improve clarity, "
                "keyword match, and measurable impact. Maintain a professional tone."
            )
            user = (
                f"JOB DESCRIPTION:\n{job_description}\n\n"
                f"ORIGINAL CV:\n{cv_text}\n\n"
                "Rewrite the CV summary and 3-5 key experience bullets. "
                "Return only the rewritten text."
            )

            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-4o-mini",
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.2,
            )

            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[openai_error:{e}] Could not generate rewrite."

    # Mock rewrite
    return (
        "Professional Summary:\n"
        "- Results-driven candidate with experience relevant to the role. "
        "Demonstrates ownership, impact, and collaboration.\n\n"
        "Key Experience:\n"
        "- Tailor bullet 1 toward the JD’s primary responsibility and include a metric.\n"
        "- Tailor bullet 2 to highlight tools/skills the JD emphasizes (e.g., keywords).\n"
        "- Tailor bullet 3 to show cross-team collaboration and measurable outcomes.\n"
    )
