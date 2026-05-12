# JD Fit Python Scripts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 `scripts/fetch_jobs.py`（爬取 104 職缺）和 `scripts/score_fit.py`（五維度公式評分），讓 SKILL.md J2/J3 步驟可以透過 Claude Code Bash tool 呼叫，取代原本不穩定的 WebFetch 方案。

**Architecture:** 兩支獨立 Python scripts，共用 `scripts/requirements.txt`。`fetch_jobs.py` 打 104 unofficial JSON API 回傳結構化職缺 JSON；`score_fit.py` 接受 Claude 提取的技能列表與候選人資訊，執行確定性公式計算回傳分數 JSON。所有 stdout 只輸出一行 JSON，log 導向 stderr。最後更新 SKILL.md J2/J3 步驟的呼叫方式。

**Tech Stack:** Python 3.9+, requests==2.31.0, pytest==7.4.3, responses==0.24.1

---

## File Structure

| 動作 | 路徑 | 職責 |
|------|------|------|
| Create | `scripts/fetch_jobs.py` | 打 104 API，回傳職缺列表 JSON |
| Create | `scripts/score_fit.py` | 公式計算五維度分數，回傳分數 JSON |
| Create | `scripts/requirements.txt` | 共用依賴 |
| Create | `tests/test_score_fit.py` | score_fit.py 的單元測試 |
| Create | `tests/test_fetch_jobs.py` | fetch_jobs.py 的單元測試（mock HTTP）|
| Create | `tests/__init__.py` | 空檔，讓 pytest 識別 tests 目錄 |
| Modify | `SKILL.md` | J2/J3 步驟改用 Bash 呼叫 scripts |

---

## Task 1: 建立專案結構與依賴

**Files:**
- Create: `scripts/requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: 建立 scripts/requirements.txt**

```
requests==2.31.0
pytest==7.4.3
responses==0.24.1
```

- [ ] **Step 2: 建立 tests/__init__.py（空檔）**

```python
```

- [ ] **Step 3: 建立 venv 並安裝依賴**

```bash
cd /Users/eric/programs/resume-optimizer
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

Expected output: `Successfully installed requests-2.31.0 pytest-7.4.3 responses-0.24.1 ...`

- [ ] **Step 4: 驗證 pytest 可執行**

```bash
python -m pytest --version
```

Expected: `pytest 7.4.3`

- [ ] **Step 5: Commit**

```bash
git add scripts/requirements.txt tests/__init__.py
git commit -m "chore: add scripts requirements and tests directory"
```

---

## Task 2: `score_fit.py` — 純函式 + TDD

**Files:**
- Create: `scripts/score_fit.py`
- Create: `tests/test_score_fit.py`

### 先寫測試

- [ ] **Step 1: 建立 tests/test_score_fit.py**

```python
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
    out = run(**{**BASE, "resume_title": "行銷企劃"})
    assert out["scores"]["title"] <= 8


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
```

- [ ] **Step 2: 執行測試，確認全部 FAIL**

```bash
cd /Users/eric/programs/resume-optimizer
source .venv/bin/activate
python -m pytest tests/test_score_fit.py -v 2>&1 | head -30
```

Expected: 全部 FAIL，錯誤為 `No such file or directory: .../scripts/score_fit.py` 或 `ModuleNotFoundError`。

### 實作 score_fit.py

- [ ] **Step 3: 建立 scripts/score_fit.py**

```python
#!/usr/bin/env python3
"""Score resume-JD fit using 5-dimension formula. Outputs single-line JSON to stdout."""

import argparse
import json
import sys

# 技能同義詞對照（小寫）
SYNONYMS = {
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "node.js": "node",
    "nodejs": "node",
    "python3": "python",
    "amazon web services": "aws",
    "typescript": "ts",
    "ts": "typescript",  # normalize both directions to one canonical form
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

# 相鄰職類對（視為「跨域但有遷移可能」，給 14 分）
ADJACENT_CATEGORIES = {
    frozenset({"engineer", "analyst"}),
    frozenset({"marketing", "product"}),
    frozenset({"manager", "product"}),
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    # Apply synonym normalization once (no recursive loop)
    return SYNONYMS.get(s, s)


def _title_category(title: str) -> str | None:
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
        return 8  # cross-domain with migration possibility
    if jc or rc:
        return 8
    return 2


def score_skills(resume_skills: list, jd_required: list, jd_preferred: list) -> tuple[int, dict]:
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


def score_exp(resume_exp: float, jd_exp: float | None) -> int:
    if jd_exp is None:
        return 20
    if resume_exp > jd_exp + 5:
        return 16  # overqualified
    if resume_exp >= jd_exp:
        return 20
    if resume_exp >= jd_exp - 1:
        return 15
    if resume_exp >= jd_exp - 2:
        return 10
    return 5


def score_salary(resume_salary: float | None, jd_min: float | None, jd_max: float | None) -> int:
    if resume_salary is None or jd_min is None or jd_max is None:
        return 7
    if resume_salary <= jd_max:
        return 10
    if resume_salary <= jd_max * 1.15:
        return 7
    return 4


def score_industry_location(
    resume_industry: str | None,
    jd_industry: str | None,
    resume_location: str,
    jd_location: str,
) -> int:
    # ── 產業（10 分）────────────────────────────────
    if not resume_industry or not jd_industry:
        industry = 7
    elif resume_industry.strip().lower() == jd_industry.strip().lower():
        industry = 10
    else:
        tech_kws = {"軟體", "網路", "電商", "it", "資訊", "科技", "tech"}
        ri_tech = any(k in resume_industry.lower() for k in tech_kws)
        ji_tech = any(k in jd_industry.lower() for k in tech_kws)
        if ri_tech and ji_tech:
            industry = 7
        else:
            industry = 4

    # ── 地區（5 分）─────────────────────────────────
    rl = resume_location.strip()
    jl = jd_location.strip()
    if rl in ("全台", "不限", "遠端") or "remote" in rl.lower() or "remote" in jl.lower():
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
        print(json.dumps({"status": "error", "errors": [str(exc)]}), ensure_ascii=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 執行測試，確認全部 PASS**

```bash
python -m pytest tests/test_score_fit.py -v
```

Expected: 全部 PASS（約 22 tests）。

若有 FAIL，先確認同義詞對照方向：`"typescript": "ts"` 和 `"ts": "typescript"` 會導致 normalize 不一致。修正方式：只保留「alias → canonical」，刪除 `"ts": "typescript"` 那行。

- [ ] **Step 5: Commit**

```bash
git add scripts/score_fit.py tests/test_score_fit.py
git commit -m "feat: add score_fit.py with 5-dimension scoring formula"
```

---

## Task 3: `fetch_jobs.py` — 104 API client + TDD

**Files:**
- Create: `scripts/fetch_jobs.py`
- Create: `tests/test_fetch_jobs.py`

### 先寫測試

- [ ] **Step 1: 建立 tests/test_fetch_jobs.py**

```python
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import fetch_jobs


# ── 純函式測試（不需 HTTP）───────────────────────────────────────────────────

def test_build_search_url_no_salary():
    url = fetch_jobs.build_search_url("前端工程師", "6001001000")
    assert "keyword=%E5%89%8D%E7%AB%AF%E5%B7%A5%E7%A8%8B%E5%B8%AB" in url or "keyword=前端工程師" in url
    assert "area=6001001000" in url
    assert "salmin" not in url


def test_build_search_url_with_salary():
    url = fetch_jobs.build_search_url("工程師", "6001001000", salary_min=40, salary_max=60)
    assert "salmin=40" in url
    assert "salmax=60" in url


def test_parse_job_list_item_full():
    raw = {
        "jobNo": "abc123",
        "jobName": "前端工程師",
        "custName": "測試科技",
        "salaryDesc": "月薪 50,000",
        "jobAddrNoDesc": "台北市",
    }
    result = fetch_jobs.parse_job_list_item(raw)
    assert result["job_code"] == "abc123"
    assert result["title"] == "前端工程師"
    assert result["company"] == "測試科技"
    assert result["salary"] == "月薪 50,000"
    assert result["location"] == "台北市"


def test_parse_job_list_item_missing_fields():
    """缺少欄位時應回傳空字串，不 raise。"""
    result = fetch_jobs.parse_job_list_item({})
    assert result["job_code"] == ""
    assert result["title"] == ""


def test_parse_job_detail_full():
    raw = {
        "jobDetail": {"jobDescription": "我們需要一位前端工程師..."},
        "condition": {
            "workExp": "3年以上",
            "edu": "大學",
            "skill": [{"description": "React"}, {"description": "TypeScript"}],
        },
    }
    result = fetch_jobs.parse_job_detail(raw)
    assert result["jd_text"] == "我們需要一位前端工程師..."
    assert "React" in result["skill_tags"]
    assert "TypeScript" in result["skill_tags"]
    assert result["exp_required"] == "3年以上"
    assert result["education"] == "大學"


def test_parse_job_detail_empty_skills():
    raw = {"jobDetail": {"jobDescription": "JD"}, "condition": {"skill": []}}
    result = fetch_jobs.parse_job_detail(raw)
    assert result["skill_tags"] == []


# ── main() 測試（mock requests.get）────────────────────────────────────────

def _make_list_response(jobs: list) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"data": {"list": jobs}}
    return resp


def _make_detail_response(job_desc: str = "JD文字") -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "data": {
            "jobDetail": {"jobDescription": job_desc},
            "condition": {"workExp": "2年以上", "edu": "大學", "skill": []},
        }
    }
    return resp


def test_main_success_output_shape(capsys):
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            _make_detail_response("職務說明內容"),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert len(out["jobs"]) == 1
    assert out["jobs"][0]["title"] == "前端工程師"
    assert out["jobs"][0]["jd_text"] == "職務說明內容"
    assert "errors" in out


def test_main_fallback_on_http_error(capsys):
    import requests as req_lib
    with patch("fetch_jobs.requests.get") as mock_get:
        err = req_lib.exceptions.HTTPError("403 Client Error")
        mock_get.side_effect = err
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "need_fallback"
    assert "search_url" in out
    assert len(out["errors"]) > 0


def test_main_detail_error_still_returns_base(capsys):
    """個別 JD 抓取失敗時，基本資訊仍回傳（jd_text 為空），不中斷整體。"""
    import requests as req_lib
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            req_lib.exceptions.HTTPError("500"),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert out["jobs"][0]["jd_text"] == ""
    assert len(out["errors"]) > 0


def test_stdout_single_json_line(capsys):
    """stdout 必須只有一行 JSON，stderr 不混入。"""
    mock_job = {
        "jobNo": "x1", "jobName": "前端工程師",
        "custName": "A公司", "salaryDesc": "面議", "jobAddrNoDesc": "台北市",
    }
    with patch("fetch_jobs.requests.get") as mock_get, \
         patch("fetch_jobs.time.sleep"):
        mock_get.side_effect = [
            _make_list_response([mock_job]),
            _make_detail_response(),
        ]
        with patch("sys.argv", ["fetch_jobs.py", "--keyword", "前端工程師", "--area", "6001001000"]):
            fetch_jobs.main()

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) == 1
    json.loads(lines[0])  # must not raise
```

- [ ] **Step 2: 執行測試，確認 FAIL**

```bash
python -m pytest tests/test_fetch_jobs.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'fetch_jobs'` 或類似錯誤。

### 實作 fetch_jobs.py

- [ ] **Step 3: 建立 scripts/fetch_jobs.py**

```python
#!/usr/bin/env python3
"""Fetch job listings from 104.com.tw unofficial JSON API. Outputs single-line JSON to stdout."""

import argparse
import json
import sys
import time

import requests

LIST_API = "https://www.104.com.tw/jobs/search/list"
DETAIL_API = "https://www.104.com.tw/job/ajax/content/{job_code}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.104.com.tw/jobs/search/",
    "Accept": "application/json, text/plain, */*",
}


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def build_search_url(keyword: str, area: str, salary_min=None, salary_max=None) -> str:
    params = {
        "keyword": keyword,
        "area": area,
        "ro": "0", "kwop": "7", "order": "15",
        "asc": "0", "page": "1", "mode": "s",
    }
    if salary_min is not None:
        params["salmin"] = str(salary_min)
    if salary_max is not None:
        params["salmax"] = str(salary_max)
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://www.104.com.tw/jobs/search/?{qs}"


def fetch_job_list(keyword: str, area: str, salary_min=None, salary_max=None, limit: int = 10) -> list:
    params = {
        "keyword": keyword, "area": area,
        "ro": "0", "kwop": "7", "order": "15",
        "asc": "0", "page": "1", "mode": "s",
        "jobsource": "2018indexpoc",
        "pagesize": str(min(limit, 20)),
    }
    if salary_min is not None:
        params["salmin"] = str(salary_min)
    if salary_max is not None:
        params["salmax"] = str(salary_max)
    resp = requests.get(LIST_API, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("list", [])[:limit]


def fetch_job_detail(job_code: str) -> dict:
    url = DETAIL_API.format(job_code=job_code)
    resp = requests.get(url, headers=HEADERS, timeout=8)
    resp.raise_for_status()
    return resp.json().get("data", {})


def parse_job_list_item(item: dict) -> dict:
    return {
        "job_code": item.get("jobNo", ""),
        "title": item.get("jobName", ""),
        "company": item.get("custName", ""),
        "salary": item.get("salaryDesc", ""),
        "location": item.get("jobAddrNoDesc", ""),
    }


def parse_job_detail(detail: dict) -> dict:
    job_info = detail.get("jobDetail", {})
    condition = detail.get("condition", {})
    skill_tags = [tag.get("description", "") for tag in condition.get("skill", [])]
    return {
        "jd_text": job_info.get("jobDescription", ""),
        "skill_tags": [s for s in skill_tags if s],
        "exp_required": condition.get("workExp", ""),
        "education": condition.get("edu", ""),
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch 104 job listings")
    p.add_argument("--keyword", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--salary-min", type=int, default=None)
    p.add_argument("--salary-max", type=int, default=None)
    p.add_argument("--limit", type=int, default=10)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    search_url = build_search_url(args.keyword, args.area, args.salary_min, args.salary_max)
    errors = []

    try:
        raw_list = fetch_job_list(
            args.keyword, args.area,
            args.salary_min, args.salary_max, args.limit,
        )
    except Exception as exc:
        _log(f"List API error: {exc}")
        print(json.dumps({
            "status": "need_fallback",
            "search_url": search_url,
            "errors": [str(exc)],
        }, ensure_ascii=False))
        return

    jobs = []
    for item in raw_list:
        base = parse_job_list_item(item)
        job_code = base["job_code"]
        try:
            time.sleep(0.5)
            detail_raw = fetch_job_detail(job_code)
            detail = parse_job_detail(detail_raw)
        except Exception as exc:
            _log(f"Detail error for {job_code}: {exc}")
            errors.append(f"job {job_code}: {exc}")
            detail = {"jd_text": "", "skill_tags": [], "exp_required": "", "education": ""}
        jobs.append({**base, **detail})

    print(json.dumps({
        "status": "success",
        "jobs": jobs,
        "errors": errors,
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _log(f"Fatal: {exc}")
        print(json.dumps({"status": "error", "errors": [str(exc)]}), ensure_ascii=False)
        sys.exit(1)
```

- [ ] **Step 4: 執行測試，確認全部 PASS**

```bash
python -m pytest tests/test_fetch_jobs.py -v
```

Expected: 全部 PASS（約 10 tests）。

- [ ] **Step 5: 執行全部測試**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASS（score_fit + fetch_jobs 合計約 32 tests）。

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_jobs.py tests/test_fetch_jobs.py
git commit -m "feat: add fetch_jobs.py for 104 job listing via unofficial JSON API"
```

---

## Task 4: 更新 SKILL.md J2/J3 步驟

**Files:**
- Modify: `SKILL.md` (JD Fit Analysis Step J2 和 Step J3 區塊)

- [ ] **Step 1: 讀取 SKILL.md 確認 J2/J3 行號**

```bash
grep -n "JD Fit Analysis Step J" /Users/eric/programs/resume-optimizer/SKILL.md
```

Expected: 印出 J1/J2/J3/J4 各自的行號。

- [ ] **Step 2: 替換 J2 步驟內容**

找到目前 `## JD Fit Analysis Step J2 — 抓取 104 職缺` 區塊（到下一個 `---` 為止），替換成：

```markdown
## JD Fit Analysis Step J2 — 抓取 104 職缺

Load `references/jd-crawl-guide.md` now.

依據 `[JF_職稱]`、`[JF_地區碼]`、`[JF_薪資]` 執行以下 Bash 指令：

```bash
python scripts/fetch_jobs.py \
  --keyword "[JF_職稱]" \
  --area [JF_地區碼] \
  [--salary-min X --salary-max Y]
```

**處理回傳的 JSON：**
- `status=success` → 從 `jobs` 陣列提取職缺清單，呈現給用戶選擇 3–5 筆
- `status=need_fallback` → 告知用戶：「104 頁面無法直接存取，請打開以下連結，把想分析的職缺 URL 或 JD 文字貼回給我：[search_url]」
- `status=error` → 告知用戶發生錯誤，請手動貼入 JD 文字

用戶選擇後，將選定的職缺 `jd_text` 保留在 context 供 J3 使用。
```

- [ ] **Step 3: 替換 J3 步驟內容**

找到目前 `## JD Fit Analysis Step J3 — 適配度評分` 區塊，替換成：

```markdown
## JD Fit Analysis Step J3 — 適配度評分

Load `references/jd-fit-scoring.md` now.

**[語氣檢查點]** 維持 `[語氣]`，所有評分說明與推薦文字全程角色狀態。

對每筆選定 JD，依以下流程計算分數：

**1. Claude 從 jd_text 提取（直接讀 context，不需額外 API call）：**
- `jd_required`：必要技能清單（JSON array）
- `jd_preferred`：加分技能清單（JSON array）
- `jd_exp`：要求年資數字（若無則省略此參數）
- `jd_salary_min` / `jd_salary_max`：薪資範圍（千元，若「面議」則省略）
- `jd_industry`：產業別
- `jd_location`：工作地點

**2. 執行 score_fit.py：**

```bash
python scripts/score_fit.py \
  --job-title "[JD職稱]" \
  --jd-required '[...]' \
  --jd-preferred '[...]' \
  [--jd-exp N] \
  [--jd-salary-min X --jd-salary-max Y] \
  --jd-industry "[產業]" \
  --jd-location "[地點]" \
  --resume-title "[JF_職稱]" \
  --resume-skills '[JF_技能池]' \
  --resume-exp [JF_年資] \
  [--resume-salary N] \
  [--resume-industry "[產業]"] \
  --resume-location "[JF_地區]"
```

收到 `status=success` → 記錄 `scores` 與 `skill_detail`，繼續下一筆 JD。

所有分數收集完畢後，依 `total` 降冪排序，進入 J4。
```

- [ ] **Step 4: 執行快速語法驗證**

```bash
grep -n "python scripts/" /Users/eric/programs/resume-optimizer/SKILL.md
```

Expected: 印出兩行，分別對應 J2 的 `fetch_jobs.py` 和 J3 的 `score_fit.py`。

- [ ] **Step 5: Commit**

```bash
git add SKILL.md
git commit -m "feat: update SKILL.md J2/J3 to use fetch_jobs.py and score_fit.py"
```

---

## Self-Review

**Spec coverage:**
| 需求 | 對應任務 |
|------|---------|
| fetch_jobs.py 打 104 JSON API | Task 3 |
| fetch_jobs.py fallback on 403 | Task 3 test_main_fallback_on_http_error |
| score_fit.py 五維度公式 | Task 2 |
| 技能同義詞對照 | Task 2 score_fit.py SYNONYMS + tests |
| stdout 只輸出一行 JSON | Task 2/3 test_stdout_single_json_line |
| requirements.txt 共用 | Task 1 |
| SKILL.md J2/J3 更新 | Task 4 |

**Placeholder scan:** 無 TBD/TODO。

**Type consistency:**
- `parse_job_list_item` 在 Task 3 定義與測試中名稱一致 ✅
- `parse_job_detail` 同上 ✅
- `score_title`/`score_skills`/`score_exp`/`score_salary`/`score_industry_location` 在 Task 2 定義與測試引用一致 ✅
- `skill_detail` 鍵名（`matched_required`/`missing_required`/`matched_preferred`/`missing_preferred`）在 score_fit.py 輸出與測試 assert 一致 ✅
