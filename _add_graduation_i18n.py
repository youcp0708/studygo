# -*- coding: utf-8 -*-
import polib, sys

en_translations = {
    '成績與畢業門檻': 'Grades & Graduation Requirements',
    'GPA・畢業門檻・英文門檻': 'GPA · Graduation Threshold · English Proficiency',
    '中央大學成績等第制度、GPA 計算方式，以及各學院畢業所需達到的英文門檻標準。': 'NCU grade letter system, GPA calculation method, and the English proficiency requirements for graduation from each college.',
    '成績等第制（109 學年起適用）': 'Grade Letter System (Effective from AY 109)',
    '109 學年（2020年9月）入學起，中央大學採等第制記錄成績，並換算為 GPA（4.3 滿分）。大學部及格標準為 60 分（C-），研究所為 70 分（B-）。': 'For students enrolled from AY 109 (September 2020) onwards, NCU records grades using letter grades converted to GPA (max 4.3). The passing standard for undergraduates is 60 (C-); for graduate students it is 70 (B-).',
    '等第': 'Grade',
    '分數範圍': 'Score Range',
    '說明': 'Notes',
    '優異': 'Excellent',
    '研究所最低及格': 'Graduate minimum pass',
    '大學部最低及格': 'Undergraduate minimum pass',
    '不及格': 'Fail',
    '0（缺考）': '0 (Absent)',
    'W（停修）': 'W (Withdrawal)',
    '不計入學分，成績單標註 W': 'Not counted in credits; transcript marked W',
    'GPA 計算方式': 'GPA Calculation Method',
    '計算公式': 'Formula',
    '課程學分數': 'Course Credits',
    '該課程等第積分': 'Grade Points for the Course',
    '總學分數': 'Total Credits',
    '中大採 4.3 滿分制。出國交換、申請研究所時，部分機構採 4.0 換算，請依對方要求換算。': 'NCU uses a 4.3-point scale. When applying for exchange programs or graduate schools, some institutions use a 4.0 scale — convert as required by the receiving institution.',
    '體育課、軍訓、服務學習不計入畢業學分，但仍有成績記錄。這些課程的 GPA 積分計算方式請洽各系確認。': 'PE, military training, and service learning are not counted toward graduation credits, but grades are still recorded. Please check with your department on how these affect your GPA calculation.',
    '畢業條件一覽（大學部）': 'Graduation Requirements Overview (Undergraduate)',
    '畢業學分數': 'Graduation Credits',
    '大多數學系需修滿 128 學分（含必修、通識、選修）。實際學分依各系課程規定，請至系網查詢應修科目表。': 'Most departments require 128 credits (including required, general education, and elective courses). Actual requirements vary by department — check your department\'s required course list.',
    '計學分': 'Counts toward credits',
    '通識課程': 'General Education',
    '至少修習 8 學分通識課程（含核心通識及通識選修）。各學院核心通識規定略有不同，請確認是否選滿必修核心。': 'At least 8 credits of general education courses (including core and elective general education) are required. Core requirements vary by college — confirm you have completed all mandatory core courses.',
    '體育課': 'Physical Education',
    '需修滿 5 學期體育課（大一必修上、下 + 興趣體育 3 學期）。不列入畢業學分，但必須修畢方可畢業。': '5 semesters of PE are required (2 mandatory in Year 1 + 3 elective PE semesters). Not counted toward graduation credits, but must be completed to graduate.',
    '不計學分': 'Not counted in credits',
    '服務學習': 'Service Learning',
    '需修滿 1 學年（上、下各一學期）。不列入畢業學分，但必須通過方可畢業。': '1 full academic year (one semester each term) is required. Not counted toward graduation credits, but must be passed to graduate.',
    '英文畢業門檻': 'English Graduation Threshold',
    '各學院標準不同（詳見下方表格）。未達標者可修習「進修英文」（4 學分，2 學期）作為替代途徑。': 'Standards differ by college (see table below). Students who do not meet the threshold may take "Supplementary English" (4 credits, 2 semesters) as an alternative.',
    '需達標': 'Must meet standard',
    '操行成績': 'Conduct Grade',
    '各學期操行成績均須及格。': 'Conduct grades must be passing every semester.',
    '英文畢業門檻（大學部，依學院）': 'English Graduation Threshold (Undergraduate, by College)',
    '以下為各學院門檻標準，實際以語言中心公告為準。部分學院允許以「第二外語」替代英文門檻，請洽語言中心確認。': 'The thresholds below are the college standards. Actual requirements follow the Language Center\'s official announcements. Some colleges allow a second foreign language as a substitute — confirm with the Language Center.',
    '學院': 'College',
    '（聽讀合計）': '(Listening + Reading)',
    '全民英檢': 'GEPT',
    '管理學院': 'College of Management',
    '中高級複試通過': 'GEPT High-Intermediate (Stage 2)',
    '文學院': 'College of Humanities',
    '客家學院': 'College of Hakka Studies',
    '電資學院': 'College of Electrical Engineering & Computer Science',
    '工學院': 'College of Engineering',
    '理學院': 'College of Science',
    '地球科學學院': 'College of Earth Sciences',
    '生醫理工學院': 'College of Biomedical Sciences & Engineering',
    '校園多益（TOEIC）考試：語言中心每學期舉辦校園多益，費用約 NT$1,270，僅限本校學生報考，是達到英文門檻最便利的方式。報名請至語言中心網站查詢最新場次。': 'Campus TOEIC: The Language Center holds a campus TOEIC exam every semester. The fee is approximately NT$1,270, open only to NCU students. It is the most convenient way to meet the English graduation requirement. Check the Language Center website for the latest session registration.',
    '未達門檻的替代方案：進修英文': 'Alternative for Not Meeting the Threshold: Supplementary English',
    '進修英文（Supplementary English）': 'Supplementary English',
    '共 4 學分，分兩學期修習（每學期 2 學分）': '4 credits total, taken over two semesters (2 credits per semester)',
    '修習並通過後可取代英文門檻，無需另外提交語言成績': 'Upon completion and passing, it substitutes for the English proficiency requirement — no separate language score needed',
    '申請資格：入學英文成績未達標準，且已參加過中央大學英文鑑定測驗者': 'Eligibility: Students whose English score at enrollment did not meet the standard and who have taken the NCU English Placement Test',
    '是否計入畢業學分依各系規定，請洽系辦確認': 'Whether it counts toward graduation credits depends on your department — confirm with the department office',
    '研究所英文門檻（以工學院為例）': 'Graduate English Threshold (College of Engineering as Example)',
    '各研究所英文門檻由各學院自訂，需於申請學位口試前繳交。以工學院為例，需達 TOEIC 600 / TOEFL iBT 64 / IELTS 5.0 或同等資格，未達標者可修習一學期補救英文課程（70分以上通過）替代。詳細規定請洽各系所。': 'Each graduate program sets its own English requirement, which must be submitted before the degree oral exam. For the College of Engineering, the requirement is TOEIC 600 / TOEFL iBT 64 / IELTS 5.0 or equivalent. Students who do not meet this can take a one-semester remedial English course (pass with 70+) instead. Please check with your department for specific regulations.',
    '語言中心英文畢業門檻': 'Language Center — English Graduation Threshold',
    'NCU 語言中心': 'NCU Language Center',
    '應修科目表': 'Required Course List',
    '教務處官網': 'Academic Affairs Office Website',
}

lang = 'en'
path = f'locale/{lang}/LC_MESSAGES/django.po'
po = polib.pofile(path)
entry_map = {e.msgid: e for e in po}
updated = added = 0
for msgid, msgstr in en_translations.items():
    if msgid in entry_map:
        if not entry_map[msgid].msgstr:
            entry_map[msgid].msgstr = msgstr
            updated += 1
    else:
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
        added += 1
po.save(path)
po.save_as_mofile(path.replace('.po', '.mo'))
sys.stdout.buffer.write(f'en: updated {updated}, added {added}\n'.encode('utf-8'))
print('Done.')
