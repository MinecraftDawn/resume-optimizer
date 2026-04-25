---
name: resume-optimizer
description: >
  Use whenever a user shares or describes a 104 履歷 (resume) or LinkedIn profile and wants it
  reviewed, scored, or improved — even if they only paste a fragment or describe it verbally.
  Triggers on: 104履歷, 履歷優化, 幫我看履歷, 履歷分析, 履歷打分, resume review Taiwan, 104 profile,
  幫我改履歷, 我的履歷怎麼樣, LinkedIn優化, LinkedIn個人頁面, 幫我看LinkedIn, LinkedIn profile
  optimization, LinkedIn分析, 幫我改LinkedIn, LinkedIn怎麼填, 如何優化LinkedIn, LinkedIn加分.
  Also applies when user wants dual-platform (104 + LinkedIn) optimization.
  Use this skill proactively whenever any resume or LinkedIn profile content appears in the
  conversation, even without an explicit request for scoring.
---

# Resume Optimizer — 104 & LinkedIn 台灣市場

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
| `references/linkedin-mode.md` | Entering Step L1 or 雙平台 routing | LinkedIn 與 104 差異、各區塊優化概覽、雙平台策略 |
| `references/linkedin-format.md` | Entering Step L1 (always load for LinkedIn) | LinkedIn 欄位清單、充足標準、缺失處理規則 |
| `references/linkedin-scoring.md` | Entering Step L2 (always load for LinkedIn) | LinkedIn 各區塊評分 rubric，總分 100 |
| `references/linkedin-suggestions.md` | Entering Step L3 (always load for LinkedIn) | Headline/About/Experience 改寫模板、JD Gap 分析格式 |
| `references/linkedin-output.md` | Entering Step L4 (always load for LinkedIn) | LinkedIn 報告模板、狀態圖示、雙平台一致性提醒 |
| `references/platform-conversion.md` | Entering Step C1 (always load for 轉換 mode) | 欄位對照表、逐欄改寫規則、輸出格式（104↔LinkedIn 雙向）|

---

## Step 0 — Version Check & 求職目標

Before anything else, ask:

> 「在開始分析之前，請問三至四件事：
> 1. 你想做什麼？
>    (104) 分析/優化 104 履歷
>    (LI)  分析/優化 LinkedIn 個人頁面
>    (雙平台) 104 + LinkedIn 都要分析
>    (轉換) 把現有 A 平台內容轉換為 B 平台格式
> 2. 這是第一次分析，還是你已經有上一份評分報告想對比改善成效？
>    （選擇「轉換」者跳過此題）
> 3. 你目前的求職目標是哪一種？
>    (A) 主動求職中，已有特定目標職缺（有 JD）
>    (B) 主動求職中，還在探索方向（沒有特定 JD）
>    (C) 被動觀望，評估轉職可能性
>    (D) 職涯轉換（目標產業/職能與現職不同）
>    (E) 留在同產業，但希望往上晉升或加薪
> 4. 你希望以哪種語氣收到回饋？
>    1. 不套用語氣　　— 維持原始分析風格
>    2. 嘴砲型損友　　— 直白、損、但真心為你好
>    3. 嘮叨的媽媽　　— 反覆叮嚀、充滿擔憂與愛
>    4. 家中的嚴父　　— 高標準、少稱讚、要你成才
>    5. 研究所教授　　— 系統分析、邏輯導向、學術腔
>    6. 十年資深HR　　— 篩選視角、市場現實、不廢話
>    7. 行政老油條　　— 職場眉角、潛規則、人生閱歷
>    8. 勵志教練　　　— 每個弱點都是機會，正能量滿點
>    9. 外商獵頭　　　— personal brand、impact、中英混搭
>    10. 社畜老前輩　　— 過來人、務實、帶點滄桑的溫暖
>    11. 補習班名師　　— 超有條理、愛拆步驟、你一定學得會」

**平台路由：**
- 用戶選 **104** → 繼續現有 Step 1–5 流程
- 用戶選 **LI（LinkedIn）** → 載入 `references/linkedin-mode.md`，跳至 **LinkedIn Step L1**，跳過 Step 1–5
- 用戶選 **雙平台** → 先完整執行 Step 1–5（104 流程），完成後告知用戶：「104 分析完成！接下來進行 LinkedIn 增量分析。」，再執行 **LinkedIn Step L1–L4**（增量模式：可重用 104 已收集的工作經歷與目標職缺資訊）（若用戶在 104 流程中途決定只做 LinkedIn，詢問確認後直接跳至 LinkedIn Step L1）
- 用戶選 **轉換** → 跳至 **Conversion Step C0**，跳過 Step 1–5 和 LinkedIn Steps

**版本檢查路由：**
- **第一次** → 繼續 Step 1
- **有舊報告** → 請用戶貼上舊報告的總分與各區塊分數，記錄後繼續 Step 1；最終輸出時加入「與上次相比」對照欄位

**求職目標記錄：** 將用戶選擇的目標類型（A/B/C/D/E）記錄為 `[目標類型]`，並在後續步驟中應用：
- A（主動求職 有JD）→ Step 3 建議優先速效改善，JD Gap 分析優先級最高；執行 ATS 相容性檢查（目標企業規模≥200人時）
- B（主動求職 無JD）→ 跳過 JD Gap 分析；Step 3 建議聚焦「廣度關鍵字覆蓋」與「可搜尋度」；工作經歷評分移除 JD 維度（見 scoring.md）
- C（被動觀望）→ 評分客觀呈現，Step 3 建議集中在高槓桿、低工時改善項目（改 1 件事最多能加幾分）；不強迫用戶大幅重寫
- D（職涯轉換）→ Step 4 排序使用「職涯轉換」模板，Step 3 強調可遷移技能；職涯成長脈絡評分使用轉換校準規則（見 scoring.md）
- E（晉升/加薪）→ 強調成果量化與管理責任；工作經歷評分使用 Mode E 管理責任加權（見 scoring.md）；Step 3 優先建議補強管理規模敘述與自傳的晉升敘事

**語氣記錄：** 將用戶選擇的語氣編號記錄為 `[語氣]`，並在所有後續文字輸出中套用（評分公式與表格結構不受影響）。若用戶選 1（不套用語氣），維持預設分析語氣，不做任何調整。若用戶在任何時候說「換成 X 語氣」（X 可為編號或語氣名稱，模糊時以最接近的選項為準並確認），立即切換。語氣定義請查閱本文件末尾的 **Tone Definitions** 章節。轉換模式（C0–C4）輸出為欄位格式，語氣套用範圍限於補充說明文字，不改動轉換後的欄位內容本體。

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
Step 0 目標類型 = B（主動求職 無JD）？
├── 是 → 使用「新加入/廣泛求職」排序模板（見 output-format.md），跳過以下決策樹
└── 否 → 繼續以下決策樹

Step 0 目標類型 = D（職涯轉換）？
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

---

## LinkedIn Step L1 — 收集 LinkedIn 資料

Load `references/linkedin-mode.md` and `references/linkedin-format.md` now.

請用戶提供 LinkedIn 個人頁面的內容，可以：
- 截圖或貼上各區塊文字
- 逐區塊描述現有內容

收到資料後，執行 **LinkedIn Missing Section Audit**（見 `linkedin-format.md` → 欄位清單與充足標準）。

若超過 4 個主要區塊（Headline、About、工作經歷、技能）標記為 ❓，暫停分析，告知用戶：「目前 LinkedIn 資訊不足以進行完整評分，建議逐區塊補充內容。」

並詢問：
1. **目標職缺：** 有沒有想投遞的職缺 JD？（有的話做 LinkedIn 關鍵字 Gap 分析）
2. **平台使用方式：** 主動投遞、被動等獵頭、或純粹個人品牌建立？
3. **候選人背景：** 應屆/新鮮人、有工作經驗、還是正在職涯轉換？（影響評分標準校準）

若為雙平台增量模式，工作經歷內容與目標職缺資訊可直接沿用 104 流程已收集的資料，不需重複詢問。

---

## LinkedIn Step L2 — LinkedIn 評分

Load `references/linkedin-scoring.md` now. 依其 **評分 Rubric** 對每個 LinkedIn 區塊評分。

若求職目標為 E（晉升/加薪），工作經歷評分加重「管理責任描述」的比重（見 `linkedin-scoring.md` → 工作經歷 → Mode E 加權）。

若求職目標為 A（有JD）→ L3 的建議優先以 JD Gap 為核心。
若求職目標為 B（無JD）→ 技能與 About 的關鍵字廣度優先於 JD 對齊。
若求職目標為 C（被動觀望）→ 評分客觀呈現，建議聚焦高槓桿低工時的改善項目。
若求職目標為 D（職涯轉換）→ About 的可遷移技能敘述與 Headline 重塑優先。

---

## LinkedIn Step L3 — LinkedIn 優化建議

Load `references/linkedin-suggestions.md` now. 依其 **建議模板** 對達成率 <75% 的區塊提供具體建議。

- 工作經歷和 About 必含 XYZ 格式改寫範例
- 若有提供 JD，執行 LinkedIn JD Gap 分析（見 `linkedin-suggestions.md` → LinkedIn JD Gap 分析）

---

## LinkedIn Step L4 — LinkedIn 輸出報告

Load `references/linkedin-output.md` now. 依其 **輸出報告格式** 產生完整報告。

若為雙平台模式，在報告末尾加入「雙平台一致性提醒」區塊（見 `linkedin-output.md` → 雙平台增量分析模式輸出）。

---

## Conversion Step C0 — 確認轉換方向

Load `references/platform-conversion.md` now.

詢問用戶：

> 「請問你要把哪個平台的內容轉換到哪個平台？
> (A) 104 履歷 → LinkedIn 個人頁面
> (B) LinkedIn 個人頁面 → 104 履歷」

記錄轉換方向後進入 C1。

---

## Conversion Step C1 — 收集來源平台內容

根據 C0 選擇的來源平台，請用戶提供內容：

**若來源為 104：**
請用戶上傳 104 履歷 PDF 或貼上所有欄位文字（個人簡介、個人特色、工作經歷、學歷、專案成就、證照、語文能力、自傳、求職條件、附件說明）。

**若來源為 LinkedIn：**
請用戶逐區塊貼上 LinkedIn 內容（Headline、About、每份工作經歷 + 技能標籤、教育背景、專案、技能清單、證照、語言、Featured 說明）。

收到後，快速確認是否有欄位明顯缺失，若有則提示用戶補充，再繼續。

---

## Conversion Step C2 — 欄位對照審計

依據 `platform-conversion.md` → **欄位對照表**（A 或 B 方向），逐欄標記：
- 🟢 直接搬移（幾乎不需改動）
- ⚠️ 需改寫（語氣/長度/格式需調整）
- ❌ 需新建（來源平台無對應欄位）
- ℹ️ 操作說明（無法直接轉換，需在平台手動設定）

向用戶簡短報告：「我將為你轉換 X 個欄位（直接搬移 N 個、改寫 N 個、新建 N 個）。」

---

## Conversion Step C3 — 逐欄轉換

依據 `platform-conversion.md` → **逐欄改寫規則**，按欄位複雜度順序執行：

1. 先處理 ⚠️ 需改寫的欄位（語氣轉換、長度調整）
2. 再處理 ❌ 需新建的欄位（Headline 或求職條件）
3. 最後整理 🟢 直接搬移的欄位（確認格式）

每個欄位產出「可直接貼入目標平台」的完整文字。

---

## Conversion Step C4 — 輸出轉換結果

依據 `platform-conversion.md` → **輸出格式** 與欄位輸出順序，產生完整轉換報告。

報告末尾加入「轉換品質提醒」（見 `platform-conversion.md` → D. 轉換品質提醒）。

完成後詢問用戶：「轉換完成！你是否希望我對目標平台的內容進行評分，確認各區塊達成率？」
- 是 → 若目標為 LinkedIn：執行 LinkedIn Step L2–L4；若目標為 104：執行 Step 2–5
- 否 → 結束
