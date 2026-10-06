-- ════════════════════════════════════════════════════════════════
-- Student Insights：給 Microsoft Fabric 使用的唯讀資料庫帳號
-- 在 Supabase Dashboard → SQL Editor 執行（需先完成 python manage.py migrate）
-- ════════════════════════════════════════════════════════════════

-- 1.（選用：只有導入 Microsoft Fabric 時才需要第 1、2 段）建立唯讀帳號
--    TODO(手動填寫)：把 <強密碼> 換成你自己產生的密碼，並存進密碼管理器
CREATE ROLE fabric_reader WITH LOGIN PASSWORD '<強密碼>';

-- 2. 只授權去識別化的分析表（不包含 StaffProfile、QuestionClassification 與任何營運資料表）
GRANT USAGE ON SCHEMA public TO fabric_reader;
GRANT SELECT ON
    public.insights_dim_student,
    public.insights_fact_student_task,
    public.insights_fact_question,
    public.insights_alert,
    public.insights_staff_access
TO fabric_reader;

-- 3.（必要，不論是否使用 Fabric 都要執行）
--    Supabase 預設會讓 anon / authenticated 角色透過 Data API（PostgREST）讀取 public schema 的新表。
--    本專案沒有使用 Supabase Data API，為避免分析表被公開存取，明確收回權限。
REVOKE ALL ON
    public.insights_dim_student,
    public.insights_fact_student_task,
    public.insights_fact_question,
    public.insights_alert,
    public.insights_staff_access,
    public.insights_staff_profile,
    public.insights_question_classification,
    public.insights_ask_log
FROM anon, authenticated;

-- 4. 驗證：以下查詢應只列出 5 張 insights_* 表
SELECT table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'fabric_reader'
ORDER BY table_name;
