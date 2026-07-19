# -*- coding: utf-8 -*-
import polib, sys

en_translations = {
    '校內系統': 'Campus Systems',
    'Portal 帳號啟用、ee-class 課程平台、學生信箱設定': 'Portal Account Activation, ee-class Course Platform, Student Email Setup',
    '三大系統快速入口': 'Quick Access to 3 Main Systems',
    '統一登入入口，選課、成績、各系統 SSO': 'Unified login portal for course registration, grades, and SSO across all campus systems',
    '課程平台：講義、作業、公告、成績查詢': 'Course platform: lecture notes, assignments, announcements, and grade lookup',
    '學生信箱': 'Student Email',
    '學號@cc.ncu.edu.tw，重要公告必看': 'StudentID@cc.ncu.edu.tw — check regularly for important notices',
    '第一步：帳號啟用': 'Step 1: Account Activation',
    'Portal 帳號預設未啟用，入學後請先完成啟用，才能使用所有校內系統。': 'Your Portal account is not activated by default. Complete activation after enrollment before using any campus system.',
    '啟用步驟': 'Activation Steps',
    '前往啟用頁面': 'Go to the Activation Page',
    '填寫資料': 'Enter Your Information',
    '學號、出生年月日，外籍生填護照號碼（非台灣身分證）': 'Student ID and date of birth. International students use passport number (not Taiwan ID).',
    '等待約 10 分鐘': 'Wait About 10 Minutes',
    '啟用完成後即可以學號 + 預設密碼（出生年月日，YYYYMMDD）登入 Portal。': 'Once activated, log in to Portal with your student ID and default password (date of birth in YYYYMMDD format).',
    '登入後立即更改密碼': 'Change Your Password Immediately After Logging In',
    '預設密碼為生日，請馬上改成強密碼，並設定信箱或手機號碼以便之後找回密碼。': 'The default password is your birthday. Change it to a strong password immediately and link an email or phone number for future password recovery.',
    '若瀏覽器顯示「Cookie 未被接受」，請換瀏覽器（建議 Chrome / Firefox）。聯絡計算機中心：分機 57771。': 'If the browser shows "Cookies not accepted", switch browsers (Chrome or Firefox recommended). Contact the Computer Center: ext. 57771.',
    '登入帳號': 'Login Account',
    '學號': 'Student ID',
    '預設密碼': 'Default Password',
    '功能': 'Features',
    '選課 / 成績': 'Course Reg. / Grades',
    '單一登入（SSO）：一組帳密進入 ee-class、信箱、圖書館等所有校內系統': 'Single Sign-On (SSO): one account and password to access ee-class, email, library, and all other campus systems',
    '選課系統（cis.ncu.edu.tw/Course/）：透過 Portal 帳號登入': 'Course Registration System (cis.ncu.edu.tw/Course/): log in with your Portal account',
    '成績查詢、修課記錄': 'Grade inquiry and course history',
    'QR Code 登入：在公用電腦可用手機掃碼，不需輸入密碼': 'QR Code login: scan with your phone on a shared computer — no need to type your password',
    '忘記密碼：透過已綁定的信箱或手機號碼重設': 'Forgot password: reset via your linked email or phone number',
    '課程平台': 'Course Platform',
    '請勿在 ee-class 自行「註冊」新帳號！一般生直接用 Portal 帳號（學號）登入即可。': 'Do NOT register a new account on ee-class yourself! Regular students simply log in with their Portal account (student ID).',
    '學號（同 Portal）': 'Student ID (same as Portal)',
    '密碼': 'Password',
    '同 Portal 密碼': 'Same as Portal password',
    '查看課程講義、教材、教授公告': 'View course lecture notes, materials, and professor announcements',
    '繳交作業、查看作業批改結果': 'Submit assignments and check graded results',
    '課程成績查詢（部分老師使用）': 'Check course grades (used by some instructors)',
    'NCUx 雲端課程：選修免費線上課程（不計學分）': 'NCUx online courses: enroll in free online courses (no credits)',
    '特殊身份登入方式': 'Login Methods for Special Student Types',
    '身份': 'User Type',
    '帳號': 'Account',
    '一般生／教職員': 'Regular Student / Faculty',
    'Portal 密碼': 'Portal Password',
    '跨校交換生': 'Inter-School Exchange Student',
    'Z 開頭臨時帳號': 'Temporary account starting with Z',
    '原校學號': 'Home School Student ID',
    '旁聽生／推廣教育': 'Auditing Student / Continuing Education',
    'Y 開頭臨時帳號': 'Temporary account starting with Y',
    '台灣身分證號': 'Taiwan National ID Number',
    'ee-class 問題聯絡：eeclass@ncu.edu.tw｜分機 57132 / 57169': 'ee-class support: eeclass@ncu.edu.tw | ext. 57132 / 57169',
    '信箱格式': 'Email Format',
    '學號@cc.ncu.edu.tw': 'StudentID@cc.ncu.edu.tw',
    '容量': 'Storage',
    '有效期限': 'Validity',
    '畢業後 5 年': '5 years after graduation',
    '學校重要公告（選課結果、成績、繳費通知）均寄到此信箱，請定期查收': 'All important school notices (course registration results, grades, payment notifications) are sent here — check regularly',
    '登入帳號：學號；密碼：同 Portal 密碼': 'Login: student ID; Password: same as Portal password',
    '非 Gmail 帳號，無法直接存取 Google 服務': 'Not a Gmail account — cannot directly access Google services',
    '手機 / 電腦設定': 'Mobile / Desktop Setup',
    '前往「設定 → 郵件 → 帳號 → 新增帳號」，選「其他」，輸入信箱與密碼，詳細步驟：': 'Go to Settings → Mail → Accounts → Add Account, choose "Other", enter your email and password. Full guide:',
    '帳號設定頁面 → 手動設定 → IMAP，詳細步驟見同上連結': 'Account settings → Manual setup → IMAP. See the same link above for full steps.',
    '忘記密碼：透過 Portal 重設，不需另行聯絡信箱管理員': 'Forgot password: reset via Portal — no need to contact the email admin separately',
    '信箱問題聯絡：ncucc@cc.ncu.edu.tw｜分機 57555 / 57566': 'Email support: ncucc@cc.ncu.edu.tw | ext. 57555 / 57566',
    '計算機中心聯絡': 'Computer Center Contact',
    '帳號 / Portal 問題': 'Account / Portal Issues',
    '分機': 'Ext.',
    '問題': 'Issues',
    '信箱問題': 'Email Issues',
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
