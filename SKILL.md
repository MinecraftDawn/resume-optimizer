---
name: resume-optimizer
description: Use whenever a user shares or describes a 104 履歷 (resume) and wants it reviewed, scored, or improved — even if they only paste a fragment or describe it verbally. Triggers on: 104履歷, 履歷優化, 幫我看履歷, 履歷分析, 履歷打分, resume review Taiwan, 104 profile, 幫我改履歷, 我的履歷怎麼樣. Also applies to LinkedIn profile optimization as a secondary mode. Use this skill proactively whenever any resume content appears in the conversation, even without an explicit request for scoring.
---

# Resume Optimizer — 104 台灣市場

Evaluate a 104 resume with **weighted section scores** reflecting real hiring impact in Taiwan. Produce specific optimization suggestions, XYZ achievement rewrites, JD keyword gap analysis, and an optimal section ordering.

---

## Reference Files

Load these files on demand — do NOT load all at once:

| File | Load when | Contains |
|------|-----------|----------|
| `references/104-format.md` | Entering Step 1 (always load) | All 104 section fields, character limits, "充足標準" per section, quick checklist |
| `references/scoring.md` | Entering Step 2 (always load) | Per-section rubrics, scoring formulas, factor tables |
| `references/suggestions.md` | Entering Step 3 (always load) | XYZ rewrite formula, JD keyword gap analysis, common high-impact fixes |
| `references/output-format.md` | Entering Step 4 (always load) | Full report template, scoring table, ordering templates, status icons, action checklist format |
| `references/salary-benchmarks.md` | Step 2 且求職條件含薪資期望 | 台灣各職類月薪基準，依職類與年資查詢 |
| `references/industry-profiles.md` | Step 2 且目標職缺產業可識別 | 產業別高價值關鍵字清單與評分側重調整 |
| `references/linkedin-mode.md` | User requests LinkedIn optimization | Headline/About/Experience/Skills format for LinkedIn |

---

## Step 0 — Version Check & 求職目標

Before anything else, ask:

> 「在開始分析之前，請問兩件事：
> 1. 這是第一次分析，還是你已經有上一份評分報告想對比改善成效？
> 2. 你目前的求職目標是哪一種？
>    (A) 主動求職中，有特定目標職缺
>    (B) 被動觀望，評估轉職可能性
>    (C) 職涯轉換（目標產業/職能與現職不同）
>    (D) 留在同產業，但希望往上晉升或加薪」

- **第一次** → 繼續 Step 1
- **有舊報告** → 請用戶貼上舊報告的總分與各區塊分數，記錄後繼續 Step 1；最終輸出時加入「與上次相比」對照欄位

**求職目標記錄：** 將用戶選擇的目標類型（A/B/C/D）記錄為 `[目標類型]`，並在後續步驟中應用：
- A（主動求職）→ Step 3 建議優先速效改善，JD Gap 分析優先級最高
- B（被動觀望）→ 評分客觀呈現，建議集中在高槓桿、低工時改善項目
- C（職涯轉換）→ Step 4 排序使用「職涯轉換」模板，Step 3 強調可遷移技能
- D（晉升/加薪）→ 強調成果量化與管理責任，建議強化自訂內容與自傳

---

## Step 1 — Collect the Resume

Load `references/104-format.md` now.

請用戶上傳 **104 履歷 PDF**（從 104 個人會員頁面下載）。若無法提供 PDF，接受純文字貼上。

收到履歷後，**先跑 Missing Section Audit**（見下方），再詢問兩個問題（可同時問）：

1. **目標職缺：** 有沒有想投遞的職缺連結或 JD 內容？（有的話做關鍵字 Gap 分析，見 `references/suggestions.md`）
2. **候選人背景：** 應屆/新鮮人、有工作經驗、還是正在轉職？

### Missing Section Audit

解析履歷後，依據 `references/104-format.md` 的欄位清單與「充足標準」，清點每個區塊的**存在狀態**與**內容充足度**。

充足度的判斷以「有效內容是否達到充足門檻」為準，不是「有沒有填滿上限」——例如專案成就有 2 筆深度描述就算充足，不需要填滿 6 筆。

**缺失/不足處理規則：**

| 情境 | 評分處理 | Step 3 行動 |
|------|---------|------------|
| 區塊完全缺失，且目標職位明確需要（如技術職缺缺附件） | 給 0 分，標記 ❌ 嚴重缺口 | 列為最高優先建議 |
| 區塊完全缺失，但屬可選項（如推薦人） | 給 0 分，標記 ⚪ 可補充 | 若分析後有增值，建議補充 |
| 區塊存在但未達充足標準（如描述過短、標籤太少） | 按實際質量評分 | 標記 ⚠️ 內容不足，Step 3 給具體補充建議 |
| 資訊不足以評估（文字截斷或 PDF 解析失敗） | 標記 ❓ 無法評估，跳過此區塊 | 提示用戶補提供內容 |

**如果超過 4 個主要區塊（工作經歷、專長、基本資料、學歷、自傳）標記為 ❓**，暫停分析，告知用戶：「目前履歷資訊不足以進行完整評分，建議提供更完整的內容或 PDF 原檔。」

---

## Step 2 — Score Each Section

Load `references/scoring.md` now.
若求職條件中有薪資期望，同時載入 `references/salary-benchmarks.md` 查詢對應職類基準。
若 Step 1 的目標職缺屬於可識別產業（科技/行銷/設計/財務/人資/業務），同時載入 `references/industry-profiles.md` 中對應的產業區塊，並在 Step 3 建議中優先使用該產業的高價值關鍵字清單。

Score every section present using section-specific max scores. Apply Missing Section Audit results directly.

**Scoring constraint:** Score based on QUALITY and CREDIBILITY, not whether fields are filled. Read actual content before assigning any score.

---

## Step 3 — Optimization Suggestions

Load `references/suggestions.md` now. (`references/104-format.md` is already loaded.)

For every section with achievement rate < 75%, provide ≥ 2 specific suggestions. For work experience and projects, always include XYZ formula rewrites.

若目標職缺為中大型企業或外商，執行 `references/suggestions.md` 中「ATS 相容性 Checklist」，並將有問題的項目加入 Step 5 的行動清單（但不計入評分表）。

When giving suggestions, reference the **充足標準** from `references/104-format.md` to give field-level specifics — e.g., "你的工作技能目前只有 1 組，建議補充到 3–4 組，例如可以加上 [具體工具]" — rather than generic "add more content" advice. The goal is to help users understand what "enough" looks like so they don't over-fill or under-fill.

If a JD was provided, run the **Keyword Gap Analysis** defined in `references/suggestions.md`.

If **Custom Sections (自訂內容)** are absent, explicitly ask:

> 「你有沒有學術發表、開源貢獻、演講、重大獎項、或有成效的側案（side project）？這些可以作為自訂內容加進履歷，最高可獲得 3 分加分，也是真正的差異化亮點。」

Only skip this prompt if custom sections already exist in the resume.

**用戶回應後的行動：**
- 用戶確認有相關成就 → 依 `references/suggestions.md` 中「自訂內容轉化模板」的對應類型，提供具體撰寫範例
- 用戶表示沒有 → 在 Step 5 報告的行動清單中略去自訂內容項目，不強迫建議

---

## Step 4 — Section Ordering

Load `references/output-format.md` now (use for this step and Step 5).

Based on candidate background (from Step 1), recommend optimal 104 section order. Use the ordering templates in `output-format.md` as your starting point, then apply this decision tree to adjust:

```
Step 0 目標類型 = C（職涯轉換）？
├── 是 → 直接使用「職涯轉換」排序模板，跳過以下決策樹
└── 否 → 繼續以下決策樹

應屆/新鮮人（< 1 年經驗）？
├── 是 → 學歷 → 專案成就 → 專長 領頭
└── 否 → 工作經歷 領頭

目標職位明確需要證照或語文？
├── 是 → 置於前段（第 3–5 位）
└── 否 → 置於後段（第 6–8 位）

有強力專案成就？
├── 是 + 技術/創意職缺 → 緊接工作經歷之後
└── 否 → 置於專長之後

自傳達成率 ≥ 75%？
├── 是 → 置於前段（第 2–3 位）
└── 否 → 後段，或建議先優化
```

Explain WHY referencing the candidate's specific strengths.

---

## Step 5 — Output

`references/output-format.md` is already loaded. Follow the output template exactly.
