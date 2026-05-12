import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "score_fit.py")
PYTHON = sys.executable


def run(**kwargs) -> dict:
    """Run score_fit.py with given kwargs as CLI args, return parsed stdout JSON."""
    cmd = [PYTHON, SCRIPT]
    for k, v in kwargs.items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


BASE = dict(
    job_title="前端工程師",
    jd_required='["React","TypeScript","Git"]',
    jd_location="台北市",
    resume_title="前端工程師",
    resume_skills='["React","TypeScript","Git"]',
    resume_exp=3.0,
    resume_location="台北市",
)


# ── 職稱匹配 ────────────────────────────────────────────────────────────────

def test_title_exact_match():
    out = run(**BASE)
    assert out["status"] == "success"
    assert out["scores"]["title"] == 25


def test_title_same_engineer_category():
    out = run(**{**BASE, "resume_title": "後端工程師"})
    assert out["scores"]["title"] == 20


def test_title_cross_domain():
    out = run(**{**BASE, "resume_title": "行政助理"})
    # 行政助理 無 category、前端工程師(engineer) 有 category — 只有一方有職類
    assert out["scores"]["title"] == 5


# ── 技能重疊 ────────────────────────────────────────────────────────────────

def test_skill_full_coverage():
    out = run(**{**BASE,
        "jd_required": '["React","TypeScript","Git"]',
        "jd_preferred": '["Docker"]',
        "resume_skills": '["React","TypeScript","Git","Docker"]',
    })
    assert out["scores"]["skill"] == 30
    assert out["skill_detail"]["missing_required"] == []
    assert out["skill_detail"]["missing_preferred"] == []


def test_skill_synonym_react_js():
    out = run(**{**BASE,
        "jd_required": '["React.js"]',
        "resume_skills": '["React"]',
    })
    assert out["skill_detail"]["missing_required"] == []


def test_skill_synonym_python3():
    out = run(**{**BASE,
        "jd_required": '["Python3"]',
        "resume_skills": '["Python"]',
    })
    assert out["skill_detail"]["missing_required"] == []


def test_skill_low_jd_info_capped_at_20():
    """JD 只有 1 項技能（< 3），skill score 上限 20。"""
    out = run(**{**BASE,
        "jd_required": '["React"]',
        "jd_preferred": '[]',
        "resume_skills": '["React","TypeScript","Git","Docker","Python","AWS"]',
    })
    assert out["scores"]["skill"] <= 20


def test_skill_partial_coverage():
    out = run(**{**BASE,
        "jd_required": '["React","TypeScript","Git"]',
        "resume_skills": '["React"]',
    })
    assert out["skill_detail"]["missing_required"] == ["git", "typescript"]
    assert 0 < out["scores"]["skill"] < 30


# ── 年資符合度 ──────────────────────────────────────────────────────────────

def test_exp_exact_match():
    out = run(**{**BASE, "jd_exp": 3, "resume_exp": 3.0})
    assert out["scores"]["exp"] == 20


def test_exp_no_requirement():
    out = run(**BASE)  # no jd_exp argument → no requirement
    assert out["scores"]["exp"] == 20


def test_exp_slight_shortage_within_1_year():
    out = run(**{**BASE, "jd_exp": 3, "resume_exp": 2.5})
    assert out["scores"]["exp"] == 15


def test_exp_shortage_1_to_2_years():
    out = run(**{**BASE, "jd_exp": 3, "resume_exp": 1.5})
    assert out["scores"]["exp"] == 10


def test_exp_shortage_over_2_years():
    out = run(**{**BASE, "jd_exp": 5, "resume_exp": 2.0})
    assert out["scores"]["exp"] == 5


def test_exp_overqualified():
    out = run(**{**BASE, "jd_exp": 1, "resume_exp": 8.0})
    assert out["scores"]["exp"] == 16


def test_exp_exactly_5_years_over():
    """恰好超過 5 年應視為 overqualified（>= 改為 >=）。"""
    out = run(**{**BASE, "jd_exp": 1, "resume_exp": 6.0})
    assert out["scores"]["exp"] == 16


# ── 薪資符合度 ──────────────────────────────────────────────────────────────

def test_salary_within_range():
    out = run(**{**BASE, "jd_salary_min": 40, "jd_salary_max": 60, "resume_salary": 50})
    assert out["scores"]["salary"] == 10


def test_salary_resume_below_jd_min():
    out = run(**{**BASE, "jd_salary_min": 50, "jd_salary_max": 70, "resume_salary": 40})
    assert out["scores"]["salary"] == 10


def test_salary_slightly_above_max():
    out = run(**{**BASE, "jd_salary_min": 40, "jd_salary_max": 60, "resume_salary": 65})
    assert out["scores"]["salary"] == 7


def test_salary_significantly_above_max():
    out = run(**{**BASE, "jd_salary_min": 40, "jd_salary_max": 60, "resume_salary": 80})
    assert out["scores"]["salary"] == 4


def test_salary_missing_gives_7():
    out = run(**BASE)  # no salary args
    assert out["scores"]["salary"] == 7


# ── 產業/地區 ───────────────────────────────────────────────────────────────

def test_location_exact_match():
    out = run(**BASE)
    # 台北市 == 台北市 → 5 pts location
    assert out["scores"]["industry_location"] >= 5


def test_location_adjacent_cities():
    out = run(**{**BASE, "resume_location": "新北市", "jd_location": "台北市"})
    location_score = out["scores"]["industry_location"]
    assert location_score >= 4  # adjacent → 4 location pts + industry pts


def test_location_cross_region():
    out = run(**{**BASE, "resume_location": "高雄市", "jd_location": "台北市"})
    location_score = out["scores"]["industry_location"]
    assert location_score <= 8  # cross-region → 1 location pt


def test_location_all_taiwan():
    out = run(**{**BASE, "resume_location": "全台"})
    # 全台 → 5 pts location
    assert out["scores"]["industry_location"] >= 5


# ── 輸出格式 ────────────────────────────────────────────────────────────────

def test_total_equals_sum_of_dimensions():
    out = run(**BASE)
    s = out["scores"]
    assert s["total"] == s["title"] + s["skill"] + s["exp"] + s["salary"] + s["industry_location"]


def test_stdout_is_valid_json_only():
    """stdout 必須只有一行 JSON，不能混入任何其他輸出。"""
    result = subprocess.run(
        [PYTHON, SCRIPT,
         "--job-title", "工程師", "--jd-required", "[]",
         "--jd-location", "台北市", "--resume-title", "工程師",
         "--resume-skills", "[]", "--resume-exp", "3.0",
         "--resume-location", "台北市"],
        capture_output=True, text=True,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["status"] == "success"


def test_skill_detail_keys_present():
    out = run(**BASE)
    detail = out["skill_detail"]
    for key in ("matched_required", "missing_required", "matched_preferred", "missing_preferred"):
        assert key in detail
