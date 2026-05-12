# JD Fit Python Scripts Design

**Date:** 2026-05-12
**Status:** Approved

---

## Goal

將 JD 適配分析流程（SKILL.md J2/J3）中需要可靠性與確定性的兩個工作，抽出為獨立 Python scripts：
1. 爬取 104 職缺資料（替換原本不穩定的 WebFetch 方案）
2. 計算五維度適配分數（替換原本靠 LLM 估算的公式計算）

LLM（Claude Code 對話中的 Claude）仍負責所有自然語言判斷：技能提取、報告撰寫、建議生成。

---

## Architecture

```
Claude Code 對話 (SKILL.md J1–J4)
  │
  ├── J1: Claude 收集履歷 + 求職條件（不變）
  │
  ├── J2: Claude → Bash → fetch_jobs.py
  │         └─ 104 unofficial JSON API
  │         └─ 回傳結構化職缺列表 (JSON stdout)
  │         └─ Claude 呈現列表，用戶選擇 3–5 筆
  │
  ├── J3: Claude 直接讀 jd_text（已在 context）→ 提取技能清單
  │       Claude 讀履歷 context → 確認技能池
  │       Claude → Bash → score_fit.py（每筆 JD 一次）
  │         └─ 純公式計算五維度分數
  │         └─ 回傳分數 + skill_detail (JSON stdout)
  │
  └── J4: Claude 拿分數 → 撰寫報告、Gap 分析（不變）
```

**分工原則：**

| 工作 | 負責方 | 理由 |
|------|--------|------|
| 打 104 JSON API | `fetch_jobs.py` | 需要 HTTP client，requests 比 WebFetch 穩定 |
| 從 jd_text 提取技能/年資/薪資 | Claude | 非結構化文字，需要 LLM 判斷 |
| 從履歷提取技能池 | Claude | 同上，且履歷已在 context |
| 五維度分數計算 | `score_fit.py` | 確定性公式，不應靠 LLM 算術 |
| 報告敘述、Gap 建議 | Claude | 需要語氣系統、上下文整合 |

---

## Project Structure

```
resume-optimizer/
├── scripts/
│   ├── fetch_jobs.py
│   ├── score_fit.py
│   └── requirements.txt
├── references/
│   ├── jd-crawl-guide.md    # 保留：Claude 的操作說明參考
│   ├── jd-fit-scoring.md    # 保留：評分 rubric 說明
│   └── ...
└── SKILL.md                 # J2/J3 步驟需更新呼叫方式
```

---

## Script 1: `fetch_jobs.py`

### 職責
打 104 unofficial JSON API，回傳結構化職缺列表。不做任何 LLM 呼叫。

### CLI 介面

```bash
python scripts/fetch_jobs.py \
  --keyword "前端工程師" \
  --area 6001001000 \
  [--salary-min 40] \
  [--salary-max 60] \
  [--limit 10]
```

**參數說明：**

| 參數 | 必填 | 說明 |
|------|------|------|
| `--keyword` | ✅ | 職稱關鍵字 |
| `--area` | ✅ | 地區碼（見 jd-crawl-guide.md）|
| `--salary-min` | ❌ | 月薪下限（千元），省略則不篩選 |
| `--salary-max` | ❌ | 月薪上限（千元），省略則不篩選 |
| `--limit` | ❌ | 回傳筆數，預設 10，最大 20 |

### 104 API Endpoints

```
# 職缺列表
GET https://www.104.com.tw/jobs/search/list
    ?keyword={keyword}&area={area}&ro=0&kwop=7&order=15&asc=0&page=1&mode=s&jobsource=2018indexpoc

# 個別 JD 詳情
GET https://www.104.com.tw/job/ajax/content/{jobCode}
```

**Request headers（避免被阻擋）：**
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.104.com.tw/jobs/search/",
    "Accept": "application/json"
}
```

**Rate limiting：** 每筆 JD 詳情請求間隔 0.5 秒，避免觸發封鎖。

### stdout 輸出格式

**成功：**
```json
{
  "status": "success",
  "jobs": [
    {
      "job_code": "abc123",
      "title": "前端工程師",
      "company": "某科技公司",
      "salary": "月薪 45,000–65,000",
      "location": "台北市",
      "jd_text": "職務描述全文...",
      "skill_tags": ["React", "TypeScript", "Node.js"],
      "exp_required": "3年以上",
      "education": "大學"
    }
  ],
  "errors": []
}
```

**失敗（104 阻擋 / timeout）：**
```json
{
  "status": "need_fallback",
  "search_url": "https://www.104.com.tw/jobs/search/?keyword=前端工程師&area=6001001000",
  "errors": ["HTTP 403 from 104 list API"]
}
```

### 輸出規則
- 所有 debug log 導向 `stderr`，stdout 只輸出一行 JSON
- Timeout 設定：list API 10 秒，個別 JD 8 秒
- 任何 unhandled exception 回傳 `{"status": "error", "errors": ["..."]}`，不 crash

---

## Script 2: `score_fit.py`

### 職責
接受 Claude 已提取的結構化技能列表與候選人資訊，執行五維度公式計算，回傳分數與技能明細。不做任何網路請求或 LLM 呼叫。

### CLI 介面

```bash
python scripts/score_fit.py \
  --job-title "前端工程師" \
  --jd-required '["React","TypeScript","Git"]' \
  --jd-preferred '["Docker","GraphQL"]' \
  --jd-exp 3 \
  --jd-salary-min 45 \
  --jd-salary-max 65 \
  --jd-industry "軟體/網路" \
  --jd-location "台北市" \
  --resume-title "前端工程師" \
  --resume-skills '["React","Vue","TypeScript","Git","Python"]' \
  --resume-exp 3.5 \
  --resume-salary 55 \
  --resume-industry "軟體/網路" \
  --resume-location "台北市"
```

**參數說明：**

| 參數 | 必填 | 說明 |
|------|------|------|
| `--job-title` | ✅ | JD 職稱 |
| `--jd-required` | ✅ | JD 必要技能（JSON array string）|
| `--jd-preferred` | ❌ | JD 加分技能（JSON array string），預設 `[]` |
| `--jd-exp` | ❌ | JD 要求年資（數字），省略視為無要求 |
| `--jd-salary-min` | ❌ | JD 薪資下限（千元），省略視為面議 |
| `--jd-salary-max` | ❌ | JD 薪資上限（千元），省略視為面議 |
| `--jd-industry` | ❌ | JD 產業別 |
| `--jd-location` | ✅ | JD 工作地點 |
| `--resume-title` | ✅ | 履歷目標職稱 |
| `--resume-skills` | ✅ | 履歷技能池（JSON array string）|
| `--resume-exp` | ✅ | 履歷總年資（數字，一位小數）|
| `--resume-salary` | ❌ | 履歷期望月薪中位數（千元），省略則薪資維度給 7 分 |
| `--resume-industry` | ❌ | 履歷目標產業 |
| `--resume-location` | ✅ | 履歷偏好地點或 "全台" |

### 五維度計算規則（對應 jd-fit-scoring.md）

**1. 職稱/職類匹配（25 分）**
- 完全相同 → 25
- 高度相關（同職類，例：前端 vs 全端）→ 20
- 同大類（例：工程師 vs 資料分析師）→ 14
- 跨域有遷移可能 → 8
- 明顯不符 → 2

職稱比對：先做完全字串比對，失敗則以 keyword 判斷（「工程師」「設計師」「經理」「分析師」等類別詞）。

**2. 技能關鍵字重疊率（30 分）**
```python
required_coverage = len(resume_skills ∩ jd_required) / max(len(jd_required), 1)
preferred_coverage = len(resume_skills ∩ jd_preferred) / max(len(jd_preferred), 1)
raw = required_coverage * 24 + preferred_coverage * 6
skill_score = min(raw, 30)

# JD 技能少於 3 項，上限改為 20
if len(jd_required) + len(jd_preferred) < 3:
    skill_score = min(skill_score, 20)
```
技能比對：小寫化 + 同義詞對照表（React/React.js、Python/Python3、AWS/Amazon Web Services）。

**3. 年資符合度（20 分）**
```python
if jd_exp is None:           score = 20
elif resume_exp >= jd_exp:   score = 20
elif resume_exp >= jd_exp-1: score = 15
elif resume_exp >= jd_exp-2: score = 10
elif resume_exp > jd_exp+5:  score = 16  # 過度資深
else:                        score = 5
```

**4. 薪資區間符合度（10 分）**
```python
if resume_salary is None or jd_salary_min is None:
    score = 7  # 缺資料，中位數
elif resume_salary <= jd_salary_max:
    score = 10
elif resume_salary <= jd_salary_max * 1.15:
    score = 7
else:
    score = 4
```

**5. 產業/地區符合度（15 分）**
- 產業（10 分）：完全符合 10、相鄰 7、跨域有遷移 4、明顯跨域 2、無偏好 7
- 地區（5 分）：完全符合 5、鄰近縣市 4、同區域 3、跨區域 1、全台/遠端 5

### stdout 輸出格式

```json
{
  "status": "success",
  "scores": {
    "title": 25,
    "skill": 22,
    "exp": 20,
    "salary": 10,
    "industry_location": 13,
    "total": 90
  },
  "skill_detail": {
    "matched_required": ["React", "TypeScript", "Git"],
    "missing_required": [],
    "matched_preferred": [],
    "missing_preferred": ["Docker", "GraphQL"]
  }
}
```

---

## SKILL.md 更新（J2/J3）

### J2 更新後流程

```
📍 JD Fit Step J2/4 — 抓取 104 職缺

Load references/jd-crawl-guide.md now.

依據 [JF_職稱]、[JF_地區碼]、[JF_薪資] 執行：

python scripts/fetch_jobs.py \
  --keyword "[JF_職稱]" \
  --area [JF_地區碼] \
  [--salary-min X --salary-max Y]

若 status=success → 呈現職缺清單，請用戶選擇 3–5 筆
若 status=need_fallback → 告知用戶並提供 search_url
若 status=error → 請用戶手動貼入 JD 文字
```

### J3 更新後流程

```
📍 JD Fit Step J3/4 — 適配度評分

Load references/jd-fit-scoring.md now.

對每筆選定 JD（使用 fetch_jobs.py 回傳的 jd_text）：
1. Claude 從 jd_text 提取：jd_required, jd_preferred, jd_exp, jd_salary, jd_industry
2. Claude 從履歷 context 確認：resume_skills, resume_exp, resume_salary, resume_industry

執行：
python scripts/score_fit.py \
  --job-title "..." \
  --jd-required '[...]' \
  --resume-skills '[...]' \
  ...（其餘參數依提取結果填入）

收集所有分數後進入 J4。
```

---

## Dependencies

`scripts/requirements.txt`:
```
requests==2.31.0
```

**Setup（首次使用）：**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
```

---

## Error Handling 原則

1. stdout 只輸出 JSON，所有 log/warning 導向 stderr
2. 任何 exception 捕捉後回傳 `{"status": "error", "errors": ["message"]}` 而非 crash
3. Claude 呼叫前應檢查 `status` 欄位，`error` 或 `need_fallback` 時切換到手動流程
4. fetch_jobs.py timeout 設定：list API 10s、個別 JD 8s

---

## What's Not In Scope

- Playwright fallback（目前不實作，若 requests 方案長期不穩再評估）
- 薪資資料庫整合（已有 references/salary-benchmarks.md，由 Claude 處理）
- 結果快取（不實作，每次重新 fetch）
- Web UI 或 API server
