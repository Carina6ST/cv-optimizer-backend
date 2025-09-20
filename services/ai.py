from core.config import settings

def improve_resume(resume_text: str, job_desc: str):
    if settings.AI_PROVIDER.lower() != "openai":
        return _mock_response(resume_text, job_desc)

    import requests, json
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return _mock_response(resume_text, job_desc)

    prompt = f"""
You are a career coach. Improve the following resume content to better match the job description.
Return JSON with keys: summary, bullets (array of 4), cover_letter.

Resume:
{resume_text[:6000]}

Job Description:
{job_desc[:4000]}
"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role":"user","content": prompt}],
        "temperature": 0.3
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        try:
            data = json.loads(content)
        except Exception:
            data = _mock_response(resume_text, job_desc)
        return {
            "summary": data.get("summary","Seasoned professional with impact."),
            "bullets": data.get("bullets", _mock_response(resume_text, job_desc)["bullets"]),
            "cover_letter": data.get("cover_letter", _mock_response(resume_text, job_desc)["cover_letter"]),
        }
    except Exception:
        return _mock_response(resume_text, job_desc)

def _mock_response(resume_text: str, job_desc: str):
    kws = list({w for w in job_desc.lower().split() if w.isalpha()})[:5]
    return {
        "summary": "Results-driven candidate aligning experience with the role, emphasizing measurable outcomes and key domain skills.",
        "bullets": [
            f"Tailored resume to highlight {', '.join(kws) or 'relevant skills'} and quantifiable impact.",
            "Optimized section ordering (Summary → Experience → Skills → Education) for ATS and clarity.",
            "Converted passive statements to action-oriented bullets using metrics (%, $, time saved).",
            "Ensured consistent formatting, tense, and parallel structure across achievements.",
        ],
        "cover_letter": "Dear Hiring Manager,\n\nI am excited to apply for this role. My background aligns strongly with the requirements, and I have a track record of delivering measurable results. I welcome the opportunity to contribute and discuss how my experience can help your team.\n\nSincerely,\nYour Name"
    }
