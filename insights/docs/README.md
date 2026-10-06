# Student Insights 上線指南

本文件說明 `insights` app 從部署到上線的每一個步驟。
標示 **【手動】** 的步驟需要你自己操作或填值。

> 規格 v1.3 起，Student Insights 全部在 Django + Supabase 內完成，**不需要 Microsoft 工具**。
> 第 1、2、4 節是必要步驟；第 3 節（Microsoft Fabric）為選用，只有日後要導入 Fabric 時才需要。

---

## 1. Django 端

### 1.1 環境變數（Render 的 Environment 與本機 `.env`）

| 變數 | 必填 | 說明 |
|---|---|---|
| `INSIGHTS_HASH_KEY` | 建議 | 產生去識別化學生代碼用的密鑰。**【手動】** 用 `python -c "import secrets; print(secrets.token_hex(32))"` 產生，設定後不要再改（改了以後代碼會全部變動，但不影響功能）。未設定時退回 `SECRET_KEY` |
| `INSIGHTS_EXCLUDED_EMAIL_DOMAINS` | 選填 | 不計入統計的測試帳號網域，逗號分隔，例如 `example.com,test.com`。**【手動】** 依你們的測試帳號填 |
| `INSIGHTS_EXCLUDED_EMAILS` | 選填 | 不計入統計的個別帳號，逗號分隔 |
| `INSIGHTS_USE_DEMO_DATA` | 選填 | `True` 時 Dashboard 顯示模擬資料（畫面會標示「示範資料」）。正式環境請勿設定 |

### 1.2 建立資料表 **【手動】**

```bash
python manage.py migrate insights
```

> 注意：本機 `manage.py`（`test` 以外）連的是 Supabase 正式資料庫。

### 1.3 補齊任務分類對照 **【手動】**

```bash
python manage.py build_insights
```

最後會列出被歸到「其他」的任務。把這些任務的 `task_code` 填進
`insights/task_categories.py` 的 `TASK_CODE_MAP`，再執行一次，直到清單只剩真的不屬於 7 大類的任務（例如銀行開戶）。

### 1.4 建立校方人員帳號 **【手動】**

1. Django Admin → 使用者 → 新增使用者（Email、姓名、密碼；角色維持「境外學生」即可）。
2. Django Admin → **校方人員** → 新增：選擇剛剛的帳號、所屬學校、（選填）Power BI 登入帳號。
3. 校方人員登入後，直接前往 `https://<網域>/insights/`。
   > 目前登入後會被導向「填寫個人資料」頁（既有登入流程未修改），請校方人員把 `/insights/` 加入書籤。

系統管理員（`role='admin'` 或 superuser）不需要建立校方人員資料，就能看全部學校。

### 1.5 每日排程 **【手動】**

專案目前沒有內建排程，`check_reminders` 也是靠外部 cron。請在 Render 新增一個 **Cron Job**（或沿用你們現有的 cron 方式）：

```bash
python manage.py classify_questions && python manage.py build_insights
```

建議時間：每天 02:00（台灣時間）。（若有導入第 3 節的 Fabric，要在 Fabric 複製資料的 03:00 之前完成。）
`classify_questions` 會用到 OpenAI（只處理關鍵字規則分不出來的提問）；若不想產生費用，加上 `--no-llm`。

### 1.6 Demo 用模擬資料（選用）

```bash
python manage.py seed_insights_demo          # 產生 1300 名模擬學生
python manage.py seed_insights_demo --clear  # 刪除模擬資料
```

模擬資料只寫入 `insights_*` 分析表（`is_demo=True`），不會碰到任何學生資料。

### 1.7 AI 資料助理（`/insights/ask/`）

- 沿用既有的 `OPENAI_API_KEY`、`OPENAI_MODEL`，不需要新的設定。沒有設定金鑰時，自由提問會停用，只能用 5 題預設問題。
- 預設問題由系統直接計算，不呼叫 OpenAI、不計入次數。
- 自由提問：每人每天最多 30 題（`insights/ask.py` 的 `DAILY_LIMIT`），每題最多呼叫 4 次分析工具（`MAX_TOOL_CALLS`）。
- 每次問答都記錄在 Django Admin →「AI 資料助理紀錄」。`數字已驗證` 為否的紀錄，代表 AI 回答中出現了工具結果裡沒有的數字，建議定期抽查。

### 1.8 CSV 匯出

「任務分析」「學生需求」「風險預警」頁上方各有一個匯出按鈕。只匯出聚合統計，分母小於 10 的格子會留空並標示「樣本不足」；校方人員只匯得出自己學校的資料。

---

## 2. Supabase：收回公開 API 權限 **【手動】**

Supabase 預設會讓 `anon` / `authenticated` 角色透過 Data API 讀取 public schema 的新資料表。
請在 Supabase Dashboard → SQL Editor 執行 [`01_fabric_readonly_role.sql`](01_fabric_readonly_role.sql) 的**第 3 段（REVOKE）**（需先完成 `migrate`）。

第 1、2 段（建立 `fabric_reader` 唯讀帳號）只有導入第 3 節的 Fabric 時才需要，屆時先把 `<強密碼>` 換成你產生的密碼。

連線資訊（Fabric 會用到）：Supabase Dashboard → Connect → **Session pooler**

| 欄位 | 值 |
|---|---|
| Server | `aws-0-<region>.pooler.supabase.com`（以 Dashboard 顯示為準） |
| Port | `5432` |
| Database | `postgres` |
| Username | `fabric_reader.<project-ref>`（pooler 的帳號格式是「角色名稱.專案代碼」） |
| Password | 上一步設定的密碼 |

> 使用 Session pooler 而不是 Direct connection：Direct connection 預設只有 IPv6，雲端服務可能連不到。

---

## 3. Microsoft Fabric（選用）**【手動】**

> 只有日後要導入 Microsoft Fabric 時才需要這一節（規格附錄 A）。

### 3.0 開工前確認

- [ ] 有付費 Fabric 容量的工作區（Data Agent 需要付費容量；試用容量可能不支援，請以 Microsoft 最新官方文件為準）
- [ ] 租戶管理員已開啟 Data Agent、Copilot、跨地理區處理等相關設定
- [ ] 報表使用者有 Power BI 授權（Pro / PPU，或工作區在容量上）
- [ ] 工作區區域：建議選擇亞太區域，並與合作學校確認資料存放位置

### 3.1 Lakehouse

工作區 → 新增 → **Lakehouse**，命名例如 `readyto_insights`。

### 3.2 Data Factory Pipeline

1. 工作區 → 新增 → **Data pipeline**（或 Copy job）。
2. 來源：**PostgreSQL**，填入第 2 節的連線資訊，啟用加密連線。
3. 複製以下 5 張表，目的地為 Lakehouse **Tables**，寫入模式選 **Overwrite**（每日全量覆寫）：
   - `public.insights_dim_student`
   - `public.insights_fact_student_task`
   - `public.insights_fact_question`
   - `public.insights_alert`
   - `public.insights_staff_access`
4. 排程：每天 03:00（台灣時間），晚於 Django 的 `build_insights`。
5. 手動執行一次，確認 Lakehouse 中各表筆數與 Supabase 一致。

### 3.3 Power BI 語意模型

1. Lakehouse → **新增語意模型**，勾選上述 5 張表。
2. 開啟模型 → 新增量值：貼上 [`02_powerbi_measures.dax`](02_powerbi_measures.dax)。
3. **列層級安全性（RLS）**：管理角色 → 新增角色 `SchoolStaff`，對下列 4 張表各加一條 DAX 篩選：

   ```dax
   -- 套用在 insights_dim_student、insights_fact_student_task、insights_fact_question、insights_alert
   [university] IN
       CALCULATETABLE (
           VALUES ( insights_staff_access[university] ),
           insights_staff_access[powerbi_upn] = LOWER ( USERPRINCIPALNAME () )
       )
   ```

   `insights_staff_access` 本身加上：

   ```dax
   [powerbi_upn] = LOWER ( USERPRINCIPALNAME () )
   ```

4. 語意模型 → 安全性 → 把校方人員（或其所屬群組）加入 `SchoolStaff` 角色。
5. 校方人員在工作區只能給 **Viewer** 權限：Admin / Member / Contributor 不受 RLS 限制，會看到全部學校。
6. 每位校方人員必須在 Django Admin 的「校方人員」填好 **Power BI 登入帳號**，下一次 `build_insights` 後才會生效。

### 3.4 Power BI 報表

建立 5 個報表頁（規格 §12.2）：

1. Overview：學生數、身份別、國籍分布（`insights_dim_student`）
2. Task Completion：矩陣「任務分類 × 身份別」，值為 `完成率`、`逾期率`
3. Overdue Trend：折線圖，X 軸 `arrival_cohort`，值為 `逾期率`，以 `task_category` 篩選
4. Student Needs：`insights_fact_question` 依 `category`、`nationality`，值為 `每百人提問數`
5. Alerts：`insights_alert` 表格（`current_label`、`current_rate`、`current_n`、`baseline_label`、`baseline_rate`、`delta_pp`、`recommendation`）

報表層級篩選：`is_demo = FALSE`。**禁止使用「發佈到 Web」**（會產生公開網址）。

### 3.5 Data Agent

依 [`03_data_agent_instructions.md`](03_data_agent_instructions.md) 設定。

---

## 4. 隱私權政策 **【手動】**

`users/templates/users/privacy_policy.html` 的「二、我們如何使用這些資訊」需要補充校務分析用途，
「三、資訊如何與第三方共享」的 OpenAI 項目需要補充說明。建議文字（請依學校法務意見調整）：

- 二、新增一點：
  > 以去識別化、彙總的方式，產生境外生行政流程的統計分析，提供合作學校的國際事務單位改善學生服務。學校人員只能看到族群層級的統計結果，無法看到個別學生的身分或對話內容。
- 三、OpenAI 項目改為：
  > **OpenAI：**處理你與 AI 聊天機器人的對話內容及上傳附件，以產生回覆；也用於將提問歸類（送出前會遮蔽電子郵件、電話、證件號碼），以及回答學校人員的統計問題（只包含彙總後的數字，不包含任何學生的姓名、電子郵件或識別碼）。
- 若日後導入第 3 節的 Fabric，再補上：
  > **Microsoft（Fabric / Power BI）**：存放與分析去識別化的統計資料，不包含姓名、電子郵件或聊天內容。

修改後需要補上 8 種語言的翻譯（`locale/*/LC_MESSAGES/django.po`）。
