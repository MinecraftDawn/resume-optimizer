#!/usr/bin/env python3
"""Score resume-JD fit using 5-dimension formula. Outputs single-line JSON to stdout."""

import argparse
import json
import sys

# 技能同義詞對照（小寫，alias → canonical）
SYNONYMS = {
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "node.js": "node",
    "nodejs": "node",
    "python3": "python",
    "amazon web services": "aws",
}

# 職稱關鍵詞 → 類別
TITLE_CATEGORIES = {
    "工程師": "engineer", "engineer": "engineer",
    "設計師": "designer", "designer": "designer",
    "分析師": "analyst", "analyst": "analyst",
    "經理": "manager", "manager": "manager", "主任": "manager",
    "行銷": "marketing", "marketing": "marketing",
    "人資": "hr", "hr": "hr",
    "業務": "sales", "sales": "sales",
    "產品": "product", "product": "product",
}

# 相鄰職類對
ADJACENT_CATEGORIES = {
    frozenset({"engineer", "analyst"}),
    frozenset({"marketing", "product"}),
    frozenset({"manager", "product"}),
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    return SYNONYMS.get(s, s)


def _title_category(title: str):
    t = title.strip().lower()
    return next((cat for kw, cat in TITLE_CATEGORIES.items() if kw in t), None)


def score_title(job_title: str, resume_title: str) -> int:
    jt = job_title.strip().lower()
    rt = resume_title.strip().lower()
    if jt == rt:
        return 25
    jc = _title_category(jt)
    rc = _title_category(rt)
    if jc and rc:
        if jc == rc:
            return 20
        if frozenset({jc, rc}) in ADJACENT_CATEGORIES:
            return 14
        return 8
    if jc or rc:
        return 5  # 只有一方有職類，跨域可能性較低
    return 2


def score_skills(resume_skills: list, jd_required: list, jd_preferred: list) -> tuple:
    r = {normalize_skill(s) for s in resume_skills}
    req = {normalize_skill(s) for s in jd_required}
    pref = {normalize_skill(s) for s in jd_preferred}

    matched_req = r & req
    missing_req = req - r
    matched_pref = r & pref
    missing_pref = pref - r

    req_coverage = len(matched_req) / max(len(req), 1)
    pref_coverage = len(matched_pref) / max(len(pref), 1)
    raw = req_coverage * 24 + pref_coverage * 6
    cap = 20 if (len(req) + len(pref)) < 3 else 30
    skill_score = min(round(raw), cap)

    detail = {
        "matched_required": sorted(matched_req),
        "missing_required": sorted(missing_req),
        "matched_preferred": sorted(matched_pref),
        "missing_preferred": sorted(missing_pref),
    }
    return skill_score, detail


def score_exp(resume_exp: float, jd_exp) -> int:
    if jd_exp is None:
        return 20
    if resume_exp >= jd_exp + 5:
        return 16
    if resume_exp >= jd_exp:
        return 20
    if resume_exp >= jd_exp - 1:
        return 15
    if resume_exp >= jd_exp - 2:
        return 10
    return 5


def score_salary(resume_salary, jd_min, jd_max) -> int:
    # jd_min 保留供未來下限檢查；目前邏輯只看 jd_max 上限
    if resume_salary is None or jd_min is None or jd_max is None:
        return 7
    if resume_salary <= jd_max:
        return 10
    if resume_salary <= jd_max * 1.15:
        return 7
    return 4


def score_industry_location(resume_industry, jd_industry, resume_location: str, jd_location: str) -> int:
    # 產業（10 分）
    if not resume_industry or not jd_industry:
        industry = 7
    elif resume_industry.strip().lower() == jd_industry.strip().lower():
        industry = 10
    else:
        tech_kws = {"軟體", "網路", "電商", "it", "資訊", "科技", "tech"}
        ri_tech = any(k in resume_industry.lower() for k in tech_kws)
        ji_tech = any(k in jd_industry.lower() for k in tech_kws)
        industry = 7 if (ri_tech and ji_tech) else 4

    # 地區（5 分）
    rl = (resume_location or "").strip()
    jl = (jd_location or "").strip()
    if not rl or not jl:
        location = 3  # 資訊不足，給中位數
    elif rl in ("全台", "不限", "遠端") or "remote" in rl.lower() or "remote" in jl.lower():
        location = 5
    elif rl == jl:
        location = 5
    else:
        NORTH = {"台北市", "新北市", "基隆市", "桃園市"}
        CENTRAL = {"台中市", "彰化縣", "南投縣", "苗栗縣"}
        SOUTH = {"台南市", "高雄市", "屏東縣", "嘉義市", "嘉義縣"}
        for group in (NORTH, CENTRAL, SOUTH):
            if rl in group and jl in group:
                location = 4
                break
        else:
            location = 1

    return industry + location


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Score resume-JD fit")
    p.add_argument("--job-title", required=True)
    p.add_argument("--jd-required", default="[]")
    p.add_argument("--jd-preferred", default="[]")
    p.add_argument("--jd-exp", type=float, default=None)
    p.add_argument("--jd-salary-min", type=float, default=None)
    p.add_argument("--jd-salary-max", type=float, default=None)
    p.add_argument("--jd-industry", default=None)
    p.add_argument("--jd-location", required=True)
    p.add_argument("--resume-title", required=True)
    p.add_argument("--resume-skills", required=True)
    p.add_argument("--resume-exp", type=float, required=True)
    p.add_argument("--resume-salary", type=float, default=None)
    p.add_argument("--resume-industry", default=None)
    p.add_argument("--resume-location", required=True)
    return p.parse_args()


def main() -> None:
    try:
        args = _parse_args()
        jd_required = json.loads(args.jd_required)
        jd_preferred = json.loads(args.jd_preferred)
        resume_skills = json.loads(args.resume_skills)

        title = score_title(args.job_title, args.resume_title)
        skill, detail = score_skills(resume_skills, jd_required, jd_preferred)
        exp = score_exp(args.resume_exp, args.jd_exp)
        salary = score_salary(args.resume_salary, args.jd_salary_min, args.jd_salary_max)
        ind_loc = score_industry_location(
            args.resume_industry, args.jd_industry,
            args.resume_location, args.jd_location,
        )

        result = {
            "status": "success",
            "scores": {
                "title": title,
                "skill": skill,
                "exp": exp,
                "salary": salary,
                "industry_location": ind_loc,
                "total": title + skill + exp + salary + ind_loc,
            },
            "skill_detail": detail,
        }
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        _log(f"ERROR: {exc}")
        print(json.dumps({"status": "error", "errors": [str(exc)]}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
