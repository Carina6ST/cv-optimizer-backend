# backend/services/ats.py
from typing import Dict, List, Set, Tuple
from collections import Counter
from rapidfuzz import process, fuzz
import re

# Light banks you can extend; keep lowercase phrases
TECH = {
    "python","java","javascript","typescript","c#","c++","go","sql","r","matlab","scala","kotlin","swift",
    "react","vue","angular","node","express","django","flask","fastapi","spring",".net","laravel","rails",
    "pandas","numpy","scikit-learn","pytorch","tensorflow","keras","nlp","llm","prompt engineering",
    "postgres","mysql","mongodb","redis","docker","kubernetes","k8s","aws","gcp","azure","ci/cd","terraform","ansible","git","linux"
}
SOFT = {
    "communication","leadership","teamwork","collaboration","problem solving","critical thinking",
    "time management","stakeholder management","presentation","negotiation","mentoring","ownership",
    "adaptability","creativity","initiative","attention to detail","empathy"
}
BUSINESS = {
    "kpi","okr","roadmap","requirements","user stories","backlog","sprint","agile","scrum",
    "stakeholder","deadline","budget","roi","compliance","regulatory"
}
EDU = {"bachelor","master","phd","msc","bsc","ba","ma","degree","diploma","certificate","certification"}
CERTS = {"aws certified","azure certified","gcp certified","pmp","scrum master","csm","itil","security+","ccna","salesforce"}
CONDITIONS = {"full-time","part-time","contract","internship","remote","hybrid","on-site","visa","relocation","travel","shift","weekend","overtime","salary","benefits"}

ALL = list(TECH | SOFT | BUSINESS | EDU | CERTS | CONDITIONS)
TOKEN_RE = re.compile(r"[A-Za-z0-9\+\#\.]+(?:\s[A-Za-z0-9\+\#\.]+)*")

REQ_MARKERS = {"must", "required", "mandatory", "need to", "have to"}
NICE_MARKERS = {"nice to have", "bonus", "plus", "preferred"}

def _norm(s: str) -> str:
    return (s or "").lower()

def _tokens(s: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(_norm(s))]

def _dedupe_keep_order(xs: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def fuzzy_find_present(text: str, bank: Set[str], threshold: int = 85) -> Set[str]:
    """Fuzzy match phrases in bank inside free text (threshold 0..100)."""
    present: Set[str] = set()
    t = _norm(text)
    for phrase in bank:
        score = fuzz.partial_ratio(phrase, t)
        if score >= threshold:
            present.add(phrase)
    return present

def fuzzy_required_optional(jd: str) -> Dict[str, Set[str]]:
    """Detect skills as required vs optional using marker windows."""
    jd_low = _norm(jd)
    required: Set[str] = set()
    optional: Set[str] = set()

    # quick windowing: split into sentences/clauses
    clauses = re.split(r"[;\n\.]", jd_low)
    for cl in clauses:
        if not cl.strip():
            continue
        in_required = any(m in cl for m in REQ_MARKERS)
        in_optional = any(m in cl for m in NICE_MARKERS)
        found = fuzzy_find_present(cl, set(ALL), threshold=88)
        if in_required:
            required |= found
        elif in_optional:
            optional |= found
        else:
            # neutral → treat as optional with lower weight
            optional |= found
    return {"required": required, "optional": optional}

def top_keywords(text: str, k: int = 25) -> List[Tuple[str,int]]:
    toks = _tokens(text)
    stop = {"the","and","a","to","of","in","for","on","with","as","by","is","are","was","were","be","an","at","or","from"}
    toks = [x for x in toks if x not in stop and len(x) >= 2]
    freq = Counter(toks)
    return freq.most_common(k)

def ats_score(cv_text: str, jd_text: str) -> Dict:
    cv_present = {
        "tech": fuzzy_find_present(cv_text, TECH),
        "soft": fuzzy_find_present(cv_text, SOFT),
        "business": fuzzy_find_present(cv_text, BUSINESS),
        "education": fuzzy_find_present(cv_text, EDU),
        "certs": fuzzy_find_present(cv_text, CERTS),
        "conditions": fuzzy_find_present(cv_text, CONDITIONS),
    }

    jd_req_opt = fuzzy_required_optional(jd_text)
    req = jd_req_opt["required"]
    opt = jd_req_opt["optional"]

    # coverage: required weighted more
    req_hit = len(req & set().union(*cv_present.values()))
    opt_hit = len(opt & set().union(*cv_present.values()))
    req_total = max(1, len(req))
    opt_total = max(1, len(opt))

    req_cov = req_hit / req_total
    opt_cov = opt_hit / opt_total

    # category coverages (helpful breakdown)
    def cov(cat: str, pool: Set[str]) -> float:
        needed = (req | opt) & pool
        return 1.0 if not needed else round(len(cv_present[cat] & needed) / max(1, len(needed)), 3)

    score = round(0.7*req_cov + 0.3*opt_cov, 3)

    # penalties: if JD mentions “must have X” and CV lacks → penalty
    hard_gaps = sorted(req - set().union(*cv_present.values()))
    penalty = min(0.25, 0.05 * len(hard_gaps))  # up to -0.25
    score = max(0.0, round(score - penalty, 3))

    return {
        "score_overall": score,
        "required_coverage": round(req_cov, 3),
        "optional_coverage": round(opt_cov, 3),
        "by_category": {
            "tech": cov("tech", TECH),
            "soft": cov("soft", SOFT),
            "business": cov("business", BUSINESS),
            "education": cov("education", EDU),
            "certs": cov("certs", CERTS),
            "conditions": cov("conditions", CONDITIONS),
        },
        "present": {k: sorted(v) for k, v in cv_present.items()},
        "jd_required": sorted(req),
        "jd_optional": sorted(opt),
        "gaps_required": hard_gaps,
        "top_keywords": {
            "cv": top_keywords(cv_text, 20),
            "jd": top_keywords(jd_text, 20),
        },
    }
