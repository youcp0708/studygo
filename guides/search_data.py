# Search body content for each guide page.
# Each page has 'zh-hant' and 'en' snippets; other languages fall back to English.
# These supplement the title/desc already in GUIDES_I18N.

SEARCH_BODY = {
    '/guides/bus-ncu/': {
        'zh-hant': [
            '公車 5617、5618：中壢火車站 ↔ 中央大學正門，車程約 20 分鐘',
            '公車 3951：中央大學 ↔ 桃園高鐵站 ↔ 桃園國際機場第一航廈',
            '桃園捷運 Green Line（綠線）：中壢站可轉乘至桃園機場',
            '校園接駁車：正門 → 宿舍區（有固定時刻表）',
            '即時公車動態查詢：Google Maps、台灣公車通 APP、Bus+ APP',
            '叫車服務：LINE TAXI、Uber、台灣大車隊 55688 均可在台使用',
            '深夜或假日：計程車或共乘 Uber 為主要選擇',
        ],
        'en': [
            'Bus 5617/5618: Zhongli Train Station ↔ NCU Main Gate, ~20 min ride',
            'Bus 3951: NCU ↔ Taoyuan HSR ↔ Taoyuan Airport Terminal 1',
            'Taoyuan Metro Green Line: transfer at Zhongli Station to reach the airport',
            'Campus shuttle: Main Gate → Dormitory area (fixed schedule)',
            'Real-time tracking: Google Maps, Taiwan Bus app, or Bus+ app',
            'Taxi/rideshare: LINE TAXI, Uber, and Taiwan Taxi 55688 available',
            'Late night or holidays: taxi or Uber is the primary option',
        ],
        'vi': [
            'Xe buýt 5617/5618: Ga Trung Lịch ↔ Cổng chính NCU, ~20 phút',
            'Xe buýt 3951: NCU ↔ Ga tàu cao tốc Đào Viên ↔ Sân bay quốc tế Đào Viên',
            'Tàu điện Taoyuan Green Line: chuyển tại Zhongli đến sân bay',
        ],
        'th': [
            'รถบัส 5617/5618: สถานี Zhongli ↔ ประตูหลัก NCU ~20 นาที',
            'รถบัส 3951: NCU ↔ สถานี Taoyuan HSR ↔ สนามบิน Taoyuan',
            'รถรางเขียว Taoyuan: เปลี่ยนที่ Zhongli ไปสนามบิน',
        ],
        'ja': [
            'バス 5617/5618：中壢駅 ↔ 中央大学正門、約20分',
            'バス 3951：中央大学 ↔ 桃園高鐵駅 ↔ 桃園国際空港第1ターミナル',
            '桃園MRTグリーンライン：中壢駅で乗り換えて空港へ',
            'キャンパスシャトル：正門 → 宿舍区（時刻表あり）',
            'タクシー/ライドシェア：LINE TAXI、Uber、台湾タクシー55688利用可',
        ],
        'ko': [
            '버스 5617/5618: 중리역 ↔ NCU 정문, 약 20분',
            '버스 3951: NCU ↔ 타오위안 고속철도역 ↔ 타오위안 국제공항 1터미널',
            '타오위안 MRT 녹색선: 중리역에서 환승하여 공항으로',
            '택시/공유차: LINE TAXI, Uber, 대만 택시 55688 이용 가능',
        ],
    },

    '/guides/emergency/': {
        'zh-hant': [
            '緊急電話：110（警察）、119（消防救護）、112（全球通用緊急）',
            '校安中心 24小時：(03) 422-7151 轉 57119 或 0963-558-941',
            '國際事務處 OIA：(03) 422-7151 轉 57100，週一至週五辦公時間',
            '衛保組：(03) 422-7151 轉 57501，平日 08:00–17:00',
            '壢新醫院急診：(03) 492-2161',
            '國際 SOS 緊急救援：可提供多語翻譯與緊急協助',
            '遇緊急狀況先撥 112，全球任何地方、任何語言均可',
        ],
        'en': [
            'Emergency numbers: 110 (Police), 119 (Fire/Ambulance), 112 (Global emergency)',
            'Campus Security 24H: (03) 422-7151 ext. 57119 or 0963-558-941',
            'International Affairs Office (OIA): (03) 422-7151 ext. 57100, weekdays',
            'Health Center: (03) 422-7151 ext. 57501, Mon–Fri 08:00–17:00',
            'Lixin Hospital ER: (03) 492-2161',
            'International SOS: multilingual emergency assistance',
            'In an emergency, dial 112 — works globally in any language',
        ],
        'vi': [
            'Số khẩn cấp: 110 (Cảnh sát), 119 (Cứu hỏa/Cấp cứu), 112 (Toàn cầu)',
            'An ninh campus 24H: (03) 422-7151 ext. 57119',
            'Văn phòng OIA: (03) 422-7151 ext. 57100',
        ],
        'th': [
            'เบอร์ฉุกเฉิน: 110 (ตำรวจ), 119 (ดับเพลิง/กู้ชีพ), 112 (ฉุกเฉินทั่วโลก)',
            'ความปลอดภัยวิทยาเขต 24 ชม.: (03) 422-7151 ต่อ 57119',
            'สำนักงาน OIA: (03) 422-7151 ต่อ 57100',
        ],
        'ja': [
            '緊急番号：110（警察）、119（消防・救急）、112（国際緊急）',
            'キャンパスセキュリティ24H：(03) 422-7151 内線57119 または 0963-558-941',
            '国際事務処OIA：(03) 422-7151 内線57100、平日のみ',
            '保健センター：(03) 422-7151 内線57501、平日08:00–17:00',
            '壢新病院救急：(03) 492-2161',
            '緊急時はまず112を。世界中どこでも、どの言語でも対応',
        ],
        'ko': [
            '긴급 번호: 110 (경찰), 119 (소방/응급), 112 (국제 긴급)',
            '캠퍼스 보안 24H: (03) 422-7151 내선 57119',
            '국제사무처 OIA: (03) 422-7151 내선 57100',
            '응급 시 112로 전화 — 전 세계 어디서나 어떤 언어로도 가능',
        ],
    },

    '/guides/graduation/': {
        'zh-hant': [
            'GPA 4.3 滿分制（109學年起），60分（C-）大學部最低及格，70分（B-）研究所最低及格',
            '大學部畢業需修滿 128 學分（含必修、通識、選修）',
            '英文門檻：管理、文、客家學院需 TOEIC 700（或 iBT 72）；理工類需 TOEIC 600（或 iBT 64）',
            '未達英文門檻可修習「進修英文」4學分（2學期）替代',
            '體育課需修滿 5 學期、服務學習需修滿 1 學年（均不計入畢業學分）',
            '校園多益（TOEIC）每學期舉辦，費用約 NT$1,270，僅限本校學生',
            '語言中心：www.lc.ncu.edu.tw',
        ],
        'en': [
            'GPA 4.3 scale (since 2020), passing: 60 (C-) undergrad, 70 (B-) graduate',
            'Undergrad needs 128 credits (required, general education, elective)',
            'English threshold: Management/Liberal Arts/Hakka need TOEIC 700 (iBT 72); Science/Engineering need TOEIC 600 (iBT 64)',
            'IELTS 5.0–5.5 also accepted; GEPT High-Intermediate stage 2 pass accepted',
            'Below threshold: take Supplementary English (4 credits, 2 semesters)',
            '5 semesters of PE and 1 year of service learning required (not counted as credits)',
            'Campus TOEIC: offered each semester, ~NT$1,270, NCU students only',
        ],
        'ja': [
            'GPA 4.3満点制（2020年度〜）、合格：学部60点（C-）、大学院70点（B-）',
            '学部卒業：128単位必要（必修・一般・選択含む）',
            '英語基準：管理・文・客家学院 TOEIC 700（iBT 72）；理工系 TOEIC 600（iBT 64）',
            '未達成の場合：補修英語4単位（2学期）で代替可',
            '体育5学期、サービスラーニング1学年 必修（卒業単位不算入）',
            'キャンパスTOEIC：毎学期実施、約NT$1,270、本学学生限定',
        ],
        'ko': [
            'GPA 4.3 만점제 (2020년부터), 합격: 학부 60점(C-), 대학원 70점(B-)',
            '학부 졸업: 128학점 필요',
            '영어 기준: 경영/문/객가대학 TOEIC 700; 이공계 TOEIC 600',
            '기준 미달 시: 보충 영어 4학점(2학기)으로 대체',
            '체육 5학기, 봉사 학습 1학년 필수 (졸업학점 미산입)',
        ],
    },

    '/guides/systems/': {
        'zh-hant': [
            'Portal 帳號：學號@cc.ncu.edu.tw，入學後在計算機中心或線上啟用',
            'ee-class（數位學習e化系統）：數位課程、作業繳交、課程資料下載',
            '學生信箱 (Gmail)：學號@g.ncu.edu.tw，入學後自動開通',
            'OWA（Outlook Web）：另有微軟 Office 365 信箱，部分系所使用',
            '計算機中心電話：(03) 422-7151 轉 57020，平日 08:00–17:00',
            '校園 WiFi：NCU 和 eduroam（國際漫遊）均可使用',
            '忘記密碼：至計算機中心 B1 服務台或線上申請重設',
        ],
        'en': [
            'Portal account: student_id@cc.ncu.edu.tw — activate at IT center or online after admission',
            'ee-class: digital learning platform for course materials, assignments, and announcements',
            'Student Gmail: student_id@g.ncu.edu.tw — activated automatically upon enrollment',
            'OWA (Outlook Web): Office 365 email, used by some departments',
            'IT Center: (03) 422-7151 ext. 57020, Mon–Fri 08:00–17:00',
            'Campus WiFi: NCU network and eduroam (international roaming) both available',
            'Forgot password: visit IT Center basement or request online reset',
        ],
        'ja': [
            'Portalアカウント：学籍番号@cc.ncu.edu.tw、入学後ITセンターまたはオンラインで有効化',
            'ee-class：デジタル学習プラットフォーム、課題提出・資料ダウンロード',
            '学生Gmail：学籍番号@g.ncu.edu.tw、入学後自動有効化',
            'ITセンター：(03) 422-7151 内線57020、平日08:00–17:00',
            'キャンパスWiFi：NCUネットワークとeduroam（国際ローミング）',
        ],
        'ko': [
            'Portal 계정: 학번@cc.ncu.edu.tw — 입학 후 IT센터 또는 온라인 활성화',
            'ee-class: 수업 자료, 과제 제출, 공지사항 확인',
            '학생 Gmail: 학번@g.ncu.edu.tw — 입학 후 자동 개통',
            'IT센터: (03) 422-7151 내선 57020',
            '캠퍼스 WiFi: NCU 네트워크 및 eduroam 사용 가능',
        ],
    },

    '/guides/housing-ncu/': {
        'zh-hant': [
            '外籍生、僑生享有宿舍優先保證，需在報到時提出申請',
            '費用：雙人房約 NT$25,000–35,000 / 學年（含水電網路）',
            '晚上 11 點（23:00）門禁，刷學生證進出',
            '宿舍區：學人宿舍（外籍生為主）、男女生舍分區管理',
            '宿舍設備：冷氣、衣櫥、書桌、網路（有線＋WiFi）',
            '校內洗衣機使用刷卡，每次約 NT$40',
            '宿舍申請截止日約入學前 2 個月，請留意校方通知',
        ],
        'en': [
            'Foreign and overseas Chinese students have guaranteed dormitory priority — apply at orientation',
            'Cost: double room ~NT$25,000–35,000 per academic year (incl. water, electricity, internet)',
            'Curfew at 11:00 PM, access with student ID card',
            'Dorm zones: International House (mainly foreign students), separate male/female floors',
            'Facilities: AC, wardrobe, desk, wired + WiFi internet',
            'Laundry machines accept card payment, ~NT$40 per load',
            'Application deadline: ~2 months before enrollment — watch for school announcements',
        ],
        'ja': [
            '外国人・僑生学生は宿舍優先保証あり — 入学時に申請',
            '費用：2人部屋 年間約NT$25,000–35,000（水道・電気・ネット込み）',
            '門限：23:00、学生証で出入り',
            '設備：エアコン、クローゼット、デスク、WiFi',
            '洗濯機：ICカード払い、1回約NT$40',
        ],
        'ko': [
            '외국인·해외 중국인 학생은 기숙사 우선 보장 — 오리엔테이션 시 신청',
            '비용: 2인실 연간 약 NT$25,000–35,000 (수도·전기·인터넷 포함)',
            '통금: 오후 11시, 학생증으로 출입',
            '시설: 에어컨, 옷장, 책상, WiFi',
        ],
    },

    '/guides/nhi/': {
        'zh-hant': [
            'ARC 核發後 4 個月開始強制加保（學生）',
            '月費：一般學生 NT$749、清寒減免最低 NT$231',
            '就診費用：門診掛號費 NT$150–300，申報後自付約 20%',
            '健保卡：第一次可於戶政事務所或醫院申請，補辦 NT$200',
            '加保地點：到校內財務室或學生事務處辦理',
            '持健保卡看診：至衛保組、診所、醫院均可刷卡',
            '健保 APP：可查詢用藥記錄、就醫記錄',
        ],
        'en': [
            'Mandatory enrollment 4 months after ARC issuance (students)',
            'Monthly premium: regular student NT$749; low-income reduction possible',
            'Out-of-pocket: NT$150–300 registration fee per visit, ~20% co-pay after claim',
            'NHI card: first issue at household registration or hospital; replacement NT$200',
            'Enrollment: go to the Student Affairs office or Finance office on campus',
            'NHI app: check prescription and medical records',
        ],
        'ja': [
            'ARC取得後4ヶ月で強制加入（学生）',
            '月額保険料：一般学生NT$749、低所得者は減額あり',
            '窓口負担：挂号費NT$150–300、申告後自己負担約20%',
            '保険証：初回は戸籍事務所または病院で申請、再発行NT$200',
            '加入手続き：キャンパスの学生課または財務課',
        ],
        'ko': [
            'ARC 발급 후 4개월부터 강제 가입 (학생)',
            '월 보험료: 일반 학생 NT$749',
            '진료비: 등록비 NT$150–300, 신청 후 약 20% 자부담',
            '건강보험증: 첫 발급은 호적사무소 또는 병원, 재발급 NT$200',
        ],
    },

    '/guides/bank/': {
        'zh-hant': [
            '統一證號 = 居留證上的「外來人口統一證號」，開戶必備',
            '郵局（台灣郵政）：全台 ATM 最多，可開台幣帳戶，窗口有中文服務',
            '台灣銀行（BOT）：部分分行有英文服務，可開外幣帳戶',
            '玉山銀行（E.Sun）：可線上開戶，支援多語言客服，有 Apple Pay/Google Pay',
            '所需文件：護照、居留證、在學證明、本人簽名',
            '開戶費：郵局免費、台灣銀行免費、玉山有最低存款要求',
            'ATM 提款：可使用 VISA/Mastercard 海外提款，手續費約 NT$75–100',
        ],
        'en': [
            'Uniform ID number = Alien Registration Number on your ARC — required for all banking',
            'Post Office (Chunghwa Post): most ATMs nationwide, TWD account, Chinese-only service',
            'Bank of Taiwan (BOT): some branches with English service, foreign currency accounts',
            "E.Sun Bank: online account opening, multilingual support, Apple Pay/Google Pay",
            'Required documents: passport, ARC, enrollment certificate, signature',
            'ATM withdrawals: VISA/Mastercard international withdrawal, fee ~NT$75–100',
        ],
        'ja': [
            '統一証号 = 居留証上の外来人口統一証号 — 口座開設に必須',
            '郵便局：全台ATM最多、台湾元口座、中国語サービスのみ',
            '台湾銀行：一部店舗に英語サービス、外貨口座可',
            '玉山銀行：オンライン口座開設可、多言語サポート',
            '必要書類：パスポート、居留証、在学証明',
        ],
        'ko': [
            '통일증호 = ARC의 외래인구 통일증호 — 개좌 개설 필수',
            '우체국: 전국 ATM 가장 많음, 대만 달러 계좌',
            '대만은행: 일부 지점 영어 서비스, 외화 계좌 가능',
            'E.Sun 은행: 온라인 계좌 개설, 다국어 지원',
        ],
    },

    '/guides/arc-foreign/': {
        'zh-hant': [
            '入台後 15 天內向移民署申請居留證（ARC）',
            '攜帶文件：護照、台灣簽證、入學許可書、健保加保費繳費單、兩吋照片 2 張',
            '健保需先到學校加保，再拿繳費收據去移民署',
            '居留證有效期：通常和在學期間一致，每年需更新',
            '移民署中壢服務站：桃園市中壢區中央西路一段109號',
            '費用：NT$1,000（首次申請）',
            '持居留證可開設銀行帳戶、辦理手機門號、申請工作許可',
        ],
        'en': [
            'Apply for ARC (Alien Residence Certificate) within 15 days of arrival in Taiwan',
            'Required: passport, Taiwan visa, admission letter, NHI enrollment payment, 2 passport photos (2 inches)',
            'Enroll in NHI at school first, then bring payment receipt to immigration',
            'ARC validity: typically matches your study period, renewed annually',
            'NIA Zhongli Service Center: No. 109, Section 1, Zhongyang W. Rd., Zhongli, Taoyuan',
            'Fee: NT$1,000 (first application)',
            'With ARC: open bank account, get phone SIM, apply for work permit',
        ],
        'vi': [
            'Nộp đơn xin ARC trong vòng 15 ngày kể từ khi đến Đài Loan',
            'Hồ sơ: hộ chiếu, visa, thư nhập học, biên lai NHI, 2 ảnh 2 inch',
            'Phí: NT$1,000 (lần đầu)',
        ],
        'th': [
            'ยื่นขอ ARC ภายใน 15 วันหลังเดินทางมาถึงไต้หวัน',
            'เอกสาร: พาสปอร์ต, วีซ่า, หนังสือรับเข้าเรียน, ใบเสร็จ NHI, รูปถ่าย 2 นิ้ว 2 รูป',
            'ค่าธรรมเนียม: NT$1,000 (ครั้งแรก)',
        ],
        'ja': [
            '入台後15日以内に移民署で居留証（ARC）を申請',
            '必要書類：パスポート、台湾ビザ、入学許可書、健保加入領収書、証明写真2枚（2インチ）',
            '健保は先に学校で加入→領収書を持って移民署へ',
            '居留証有効期：通常在学期間と同じ、毎年更新',
            '中壢サービスセンター：桃園市中壢区中央西路一段109号',
            '手数料：NT$1,000（初回）',
        ],
        'ko': [
            '대만 도착 후 15일 이내에 이민서에서 ARC 신청',
            '필요 서류: 여권, 대만 비자, 입학 허가서, 건강보험 납부 영수증, 증명사진 2장(2인치)',
            '건강보험 먼저 학교에서 가입 → 영수증 지참하여 이민서 방문',
            '수수료: NT$1,000 (최초 신청)',
        ],
    },

    '/guides/arc-overseas/': {
        'zh-hant': [
            '僑生持外國護照入台，居留證申請流程與外籍生相同',
            '所需文件：護照、僑生身分證明、連保書（由學校或OIA提供）、在學證明、照片',
            '連保書需先至國際事務處辦理，再前往移民署',
            '持居留證可申請健保、打工許可等',
        ],
        'en': [
            'Overseas Chinese students enter with foreign passport, same ARC process as foreign students',
            'Required: passport, overseas Chinese status proof, guarantor form (from school/OIA), enrollment cert, photos',
            'Guarantor form: obtain from OIA first, then visit immigration office',
            'With ARC: apply for NHI, work permit, etc.',
        ],
    },

    '/guides/arc-exchange/': {
        'zh-hant': [
            '港澳生持台灣核發之入出境許可證（台灣通行證）入台就讀',
            '可申請轉為居留申請，享有與外籍生相同的健保與工讀資格',
            '健保：ARC 或入出境許可滿 4 個月後可加保',
            '打工：取得工作許可後每週最多 20 小時',
            '台灣通行證（台灣地區入出境許可證）請至移民署或香港/澳門辦事處申請',
        ],
        'en': [
            'HK/Macau students enter with Taiwan Entry Permit (台灣通行證)',
            'Can apply to convert to ARC residency, same NHI and work rights as foreign students',
            'NHI: eligible after 4 months with ARC or entry permit',
            'Work permit: max 20 hours/week after obtaining permit',
        ],
    },

    '/guides/medical/': {
        'zh-hant': [
            '衛保組（校醫）：(03) 422-7151 轉 57501，周一至周五 08:00–17:00，免費或低費看診',
            '壢新醫院：桃園市中壢區延平路150號，急診 (03) 492-2161，提供多語翻譯',
            '敏盛醫院中壢院區：桃園市中壢區延平路155號，急診 24 小時',
            '近校西藥房、診所：後門商圈附近有多家西醫診所',
            '牙科、身心科、婦科均可使用健保卡就診',
            '持健保卡就診：掛號費約 NT$150–300，部分項目自付差額',
            '夜間或假日急症：優先前往壢新醫院急診',
        ],
        'en': [
            'Campus Health Center: (03) 422-7151 ext. 57501, Mon–Fri 08:00–17:00, free/low-cost consultations',
            'Lixin Hospital: 150 Yanping Rd., Zhongli, Taoyuan; ER (03) 492-2161; multilingual support',
            'Minsheng Hospital Zhongli: 155 Yanping Rd., 24H emergency',
            'Clinics near campus: several near the back gate commercial area',
            'NHI card accepted for dental, psychiatry, gynecology visits',
            'NHI co-pay: registration fee NT$150–300 per visit',
        ],
        'ja': [
            '保健センター：(03) 422-7151 内線57501、月–金 08:00–17:00',
            '壢新病院：桃園市中壢区延平路150号、救急 (03) 492-2161、多言語対応',
            '歯科・精神科・婦人科も健保カードで受診可',
        ],
        'ko': [
            '보건센터: (03) 422-7151 내선 57501, 월–금 08:00–17:00',
            '壢新병원: 타오위안시 중리구 옌핑로 150호, 응급 (03) 492-2161, 다국어 지원',
            '치과, 정신과, 부인과 모두 건강보험카드로 진료 가능',
        ],
    },

    '/guides/library/': {
        'zh-hant': [
            '借書上限 30 本，借閱期間 14 天，可線上續借兩次',
            '學術資料庫：JSTOR、Web of Science、ScienceDirect、華藝線上圖書館（CEPS）、Scopus',
            'K書中心（自習室）：需刷學生證入場，24小時開放（部分區域）',
            '列印費用：黑白 NT$2/張、彩色 NT$8/張，刷學生證扣款',
            '電子書借閱：HyRead、EBSCO 等平台，校外可透過 VPN 存取',
            '圖書館電話：(03) 422-7151 轉 57001',
            '跨館借閱（ILL）：可向其他大學借書，費用免費，7–14 個工作天',
        ],
        'en': [
            'Borrow limit: 30 books, 14-day loan period, 2 online renewals allowed',
            'Databases: JSTOR, Web of Science, ScienceDirect, CEPS, Scopus',
            'Study room (K-study center): requires student ID, some areas open 24H',
            'Printing: B&W NT$2/page, color NT$8/page, deducted from student ID card',
            'E-books: HyRead, EBSCO platforms; off-campus access via VPN',
            'Library phone: (03) 422-7151 ext. 57001',
            'Inter-library loan (ILL): free, 7–14 business days',
        ],
        'ja': [
            '貸出上限30冊、14日間、オンライン2回延長可',
            'データベース：JSTOR、Web of Science、ScienceDirect、CEPS、Scopus',
            '自習室（K書中心）：学生証で入室、一部24時間開放',
            '印刷：白黒NT$2/枚、カラーNT$8/枚',
            '図書館：(03) 422-7151 内線57001',
        ],
        'ko': [
            '대출 한도: 30권, 14일, 온라인 2회 연장 가능',
            '데이터베이스: JSTOR, Web of Science, ScienceDirect, CEPS, Scopus',
            '자습실: 학생증 필요, 일부 지역 24시간 운영',
            '인쇄: 흑백 NT$2/장, 컬러 NT$8/장',
        ],
    },

    '/guides/scholarship/': {
        'zh-hant': [
            '僑生獎學金：僑委會提供，每月最高 NT$5,000–10,000，每年 9–10 月申請',
            '教育部清寒補助：學費減免，每學期申請，需提交收入證明',
            '校內緊急助學金：臨時困難可向學生事務處申請',
            '境外生獎學金：部分學院依成績提供，需 GPA 3.0 以上',
            '外部獎學金：台積電、鴻海、各縣市政府等企業及地方政府設有獎學金',
            '申請文件：在學證明、成績單、財力證明（依各項目不同）',
        ],
        'en': [
            "Overseas Chinese Scholarship (OCAC): up to NT$5,000–10,000/month, apply September–October",
            'MOE financial aid: tuition reduction, apply each semester with income proof',
            'Emergency student relief: temporary hardship — apply at Student Affairs office',
            'College scholarships: GPA 3.0+ required for most',
            'External scholarships: TSMC, Foxconn, county governments offer various scholarships',
        ],
        'ja': [
            '僑生奨学金（OCAC）：月額最大NT$5,000–10,000、9–10月申請',
            '教育部低所得支援：学費減額、毎学期申請、収入証明必要',
            '学内緊急奨学金：緊急困窮時は学生課に相談',
        ],
        'ko': [
            '화교 장학금 (OCAC): 월 최대 NT$5,000–10,000, 9–10월 신청',
            '교육부 경제적 지원: 학비 감면, 매 학기 소득증명 제출',
            '교내 긴급 장학금: 긴급 상황 시 학생처에 문의',
        ],
    },

    '/guides/sim/': {
        'zh-hant': [
            '主要電信：中華電信（CHT）、遠傳（FarEasTone）、台灣大哥大（TWM）',
            '辦理需帶：護照 + 居留證（ARC），部分業者可只持護照辦預付卡',
            '預付卡（SIM卡）：NT$300–500，包含 3GB–10GB 數據，90天有效',
            '月租方案：不限量上網 + 通話，約 NT$499–599 / 月',
            '學生方案（中華電信）：約 NT$399 / 月，需學生證',
            '4G/5G 覆蓋率高，校園及宿舍均有良好訊號',
            '可在電信公司門市、7-ELEVEN、全家便利商店購買預付卡',
        ],
        'en': [
            'Major carriers: Chunghwa Telecom (CHT), Far EasTone, Taiwan Mobile (TWM)',
            'Required: passport + ARC; prepaid SIM may only need passport',
            'Prepaid SIM: NT$300–500, 3–10GB data, valid 90 days',
            'Monthly unlimited plan: NT$499–599/month (data + calls)',
            'Student plan (CHT): ~NT$399/month with student ID',
            '4G/5G good coverage on campus and in dormitories',
            'Buy prepaid SIM at carrier stores, 7-ELEVEN, or FamilyMart',
        ],
        'ja': [
            '主要キャリア：中華電信（CHT）、遠伝、台湾大哥大（TWM）',
            'SIMカード申込：パスポート＋居留証が必要。プリペイドはパスポートのみの場合も',
            'プリペイドSIM：NT$300–500、3–10GBデータ、90日有効',
            '月額無制限プラン：NT$499–599/月',
            '学生プラン（CHT）：約NT$399/月（学生証必要）',
        ],
        'ko': [
            '주요 통신사: 중화전신(CHT), 위성전기, 대만대가대(TWM)',
            '신청 필요: 여권 + ARC, 선불 SIM은 여권만으로도 가능',
            '선불 SIM: NT$300–500, 3–10GB, 90일 유효',
            '월정액 무제한 요금제: NT$499–599/월',
            '학생 요금제 (CHT): 약 NT$399/월',
        ],
    },

    '/guides/map/': {
        'zh-hant': [
            '校內餐廳：松苑餐廳（學生活動中心旁）、松果餐廳（南宿附近）',
            '校內超商：7-ELEVEN（中央大學店）位於學生活動中心',
            '小木屋鬆餅：圖書館旁，提供鬆餅、飲料',
            '後門商圈：宿舍後門出去，有多家餐廳、手搖茶飲、小吃',
            '宵夜街：後門外，深夜營業的餐飲集中區',
            '中大夜市商圈：中央路附近，多種平價選擇',
            '龍岡美食廣場：中壢龍岡，泰緬料理特色聚集地',
            '大江購物中心：離校約 10 分鐘，含 SOGO、各大餐廳、電影院',
        ],
        'en': [
            'On-campus restaurants: Songyuan (near Student Center), Songguo (near south dorm)',
            '7-ELEVEN: on campus at the Student Activity Center',
            'Little Cabin Waffles: near the library',
            'Back gate area: restaurants, bubble tea, snacks near the dorm back gate',
            'Night snack street: late-night food area outside the back gate',
            'Longgang food plaza: Thai/Burmese cuisine cluster in Zhongli Longgang',
            'Dayeh shopping center: ~10 min away, SOGO, restaurants, cinema',
        ],
        'ja': [
            'キャンパス内食堂：松苑（学生センター近く）、松果（南宿近く）',
            '7-ELEVEN：学生活動センター内にあり',
            '裏門商店街：宿舍裏門を出ると飲食店・タピオカ・軽食多数',
            '龍岡グルメ広場：タイ・ミャンマー料理の集積地',
            '大江ショッピングセンター：学校から約10分、SOGOや映画館あり',
        ],
        'ko': [
            '캠퍼스 내 식당: 松苑(학생센터 근처), 松果(남쪽 기숙사 근처)',
            '7-ELEVEN: 학생활동센터 내',
            '후문 상권: 기숙사 후문 나가면 음식점, 버블티, 분식',
            '龍岡 먹거리 광장: 태국·미얀마 요리 집결지',
            '다예 쇼핑센터: 학교에서 약 10분, SOGO, 음식점, 영화관',
        ],
    },

    '/guides/work-permit/': {
        'zh-hant': [
            '每週工作時數上限：20小時（含假日與寒暑假）',
            '申請工作許可需備：在學證明、居留證、護照、聘僱契約書',
            '向勞動部（WDA）線上申請，約需 3 個工作週',
            '違規最高罰款：NT$150,000，情節嚴重者可撤銷居留許可',
            '工作場所限制：不得從事製造業生產線工作',
            '研究生 RA/TA：需個別確認是否需申請許可，依情況而定',
        ],
        'en': [
            'Max 20 hours/week (including holidays and semester breaks)',
            'Required for application: enrollment cert, ARC, passport, employment contract',
            'Apply online to Workforce Development Agency (WDA), ~3 weeks processing',
            'Violation fine: up to NT$150,000; ARC may be revoked in serious cases',
            'Restriction: cannot work in manufacturing production lines',
            'Graduate RA/TA: confirm with your department whether a permit is needed',
        ],
    },

    '/guides/mental-health/': {
        'zh-hant': [
            '諮商中心電話：(03) 422-7151 轉 57078，每週可預約 1–2 次',
            '安心專線（24小時）：1925（按 2 可轉英語服務）',
            '自殺防治專線：1925 或 0800-788-995',
            '諮商服務：一對一輔導、壓力管理、人際困擾、情緒調適',
            '身心科就醫：可持健保卡前往壢新醫院或附近診所',
            'LINE@生命線：可文字諮詢，較適合不想說話的時候',
        ],
        'en': [
            'Counseling Center: (03) 422-7151 ext. 57078, book 1–2 sessions/week',
            '24H hotline (Chinese): 1925 (press 2 for English)',
            'Suicide prevention: 1925 or 0800-788-995',
            'Services: 1-on-1 counseling, stress, relationships, emotional support',
            'Psychiatry: use NHI card at Lixin Hospital or local clinics',
        ],
        'ja': [
            'カウンセリングセンター：(03) 422-7151 内線57078、週1–2回予約可',
            '24時間ホットライン（中国語）：1925（英語は2を押す）',
            '一人で悩まず、まずは連絡を',
        ],
        'ko': [
            '상담센터: (03) 422-7151 내선 57078, 주 1–2회 예약 가능',
            '24H 핫라인(중국어): 1925 (영어는 2번)',
            '자살 예방: 1925 또는 0800-788-995',
        ],
    },

    '/guides/regulations/': {
        'zh-hant': [
            '外籍生居留：依入出國及移民法，持有效居留證方可長期居台',
            '健保：ARC 取得後 4 個月強制加保，月費約 NT$749',
            '工讀上限：每週 20 小時，需事先申請工作許可',
            '學籍規定：修業年限最長：大學 6 年、碩士 4 年、博士 8 年',
            '中途退學者，60天內需離台或申請其他居留許可',
            '重要法規：入出國及移民法、就業服務法、全民健康保險法',
        ],
        'en': [
            'Residency: valid ARC required for extended stay, per Immigration Act',
            'NHI: mandatory enrollment 4 months after ARC, ~NT$749/month',
            'Work limit: 20 hours/week, work permit required in advance',
            'Max study period: 6 years undergraduate, 4 years master, 8 years PhD',
            'Upon withdrawal: must leave or apply for new residency within 60 days',
        ],
    },

    '/guides/course/': {
        'zh-hant': [
            '選課期間：開學前 1–2 週，每天 24 小時開放線上選課',
            '加退選：開學後第 1–2 週，可線上辦理加選或退選',
            '人工加退選：需系主任或老師簽名，至教務處辦理',
            '停修（W）：約第 12 週截止，不退學費，成績單標示 W',
            '必修課未通過：須重修，影響畢業年限',
            '暑期課程：6–8 月，可加速修業進度',
        ],
        'en': [
            'Registration: 1–2 weeks before semester starts, 24H online access',
            'Add/drop: first 1–2 weeks of semester, online',
            'Manual add/drop: needs department chair or instructor signature, submit to academic affairs',
            'Withdrawal (W): deadline around week 12, no refund, W shows on transcript',
            'Failed required course: must retake, affects graduation timeline',
            'Summer courses: June–August, accelerate your degree',
        ],
    },

    '/guides/enrollment/': {
        'zh-hant': [
            '休學：最多 2 年，需於學期開始前申請，休學期間可留台但需維持居留許可',
            '復學：復學申請在預計復學學期開學前 1 個月提出',
            '轉系：每年 3–4 月申請，需原系、目標系同意，且 GPA 通常有要求',
            '雙主修：申請門檻約 GPA 2.3 以上，需修完兩個學系的必修課',
            '輔修：修完輔修學系規定學分可取得輔修證明',
        ],
        'en': [
            'Leave of absence: max 2 years, apply before semester start; can stay in Taiwan with valid residency',
            'Reinstatement: apply 1 month before target semester starts',
            'Department transfer: apply March–April, needs approval from both departments',
            'Double major: typically requires GPA 2.3+, complete all required courses for both majors',
            'Minor: complete required credits for a minor program',
        ],
    },

    '/guides/admin-docs/': {
        'zh-hant': [
            '在學證明書（中英文）：教務處申請，免費，約 3–5 個工作天',
            '成績單（中英文）：教務處，NT$30 /份，約 3–5 個工作天',
            '中英文推薦信：由教授開立，建議提前 2–4 週告知，含學習表現摘要',
            '畢業證書：畢業後可於教務處領取，補發 NT$200',
        ],
        'en': [
            'Enrollment certificate (CN/EN): Academic Affairs, free, ~3–5 business days',
            'Transcript (CN/EN): Academic Affairs, NT$30/copy, ~3–5 business days',
            'Recommendation letter: request from professor 2–4 weeks in advance',
            'Diploma: collect at Academic Affairs after graduation; replacement NT$200',
        ],
    },

    '/guides/admissions/': {
        'zh-hant': [
            '申請資格：高中畢業或同等學歷，成績優良',
            '申請時程：每年 11 月至隔年 3 月（依海外聯招會時程）',
            '語言要求：中文 TOCFL B1（中級）以上或相關學科英文授課',
            '所需文件：高中成績單、畢業證書、語言成績、動機信',
            '學費：約 NT$50,000–70,000 / 學年（依學院不同）',
            '海外聯招會：ujsis.scu.edu.tw',
        ],
        'en': [
            'Requirements: high school diploma or equivalent, strong academic record',
            'Application period: November to March each year (per Overseas Enrollment Committee)',
            'Language: TOCFL B1 or above; some programs offer English-taught courses',
            'Required documents: high school transcripts, diploma, language scores, motivation letter',
            'Tuition: approx. NT$50,000–70,000/year (varies by college)',
            'Overseas Joint Enrollment: ujsis.scu.edu.tw',
        ],
    },

    '/guides/national-area/': {
        'zh-hant': [
            '香港、澳門：入出境許可證，可轉換居留身分',
            '馬來西亞：海外聯招會申請，STPM/SPM 成績',
            '泰國：FPAS 申請，學測或 GPA 成績',
            '越南：海外聯招會，高中或大學成績',
            '印尼：海外聯招會，各省考試成績',
            '緬甸：海外聯招會，高中成績',
            '各國申請詳情請參考海外聯招會網站：ujsis.scu.edu.tw',
        ],
        'en': [
            'Hong Kong/Macau: Taiwan entry permit, can convert to ARC residence',
            'Malaysia: Overseas Joint Enrollment, STPM/SPM scores',
            'Thailand: FPAS application, high school GPA',
            'Vietnam, Indonesia, Myanmar: Overseas Joint Enrollment Committee',
            'See ujsis.scu.edu.tw for country-specific requirements',
        ],
    },
}
