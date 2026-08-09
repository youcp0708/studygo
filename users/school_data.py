"""
users/school_data.py

各校校務資料的查核結果。這份檔案是 School / SchoolUnit 的資料來源，
由 `python manage.py seed_schools` 載入。

規則（很重要，請維持）：
1. 只寫「實際在官方網站上看到」的內容。查不到就留 None，不要填看起來合理的數字。
   學生會照著這裡的分機直接撥號，猜錯號碼比沒有號碼更糟。
2. 每一所學校都要標 source（查證用的官方網址）與 verified（查證日期）。
3. units 是校內單位，name 用學生會講的名稱，location 要能讓人走到。

尚未查證的學校不會出現在這裡；seed_schools 會照樣建立基本資料列
（校名與簡稱），其餘欄位留白並顯示為「尚未查核」。
"""

from datetime import date

_V = date(2026, 7, 29)

# code: 各欄位；未查到的欄位一律省略（不要填 None 以外的猜測值）
VERIFIED_SCHOOLS = {
    'NTU': {
        'address': '106319 臺北市大安區羅斯福路四段1號',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '02-3366-2007',
        'intl_office_url': 'https://oia.ntu.edu.tw/',
        'website': 'https://www.ntu.edu.tw/',
        'source': 'https://oia.ntu.edu.tw/contactOIA',
        'verified': _V,
        'calendar_url': 'https://www.aca.ntu.edu.tw/w/aca/calendar',
        'links': [
            {'category': 'portal', 'name': 'myNTU 臺大人入口網',
             'aliases': 'myNTU,入口網,校務系統,portal', 'url': 'https://my.ntu.edu.tw/'},
            {'category': 'lms', 'name': 'NTU COOL 數位教學平台',
             'aliases': 'NTU COOL,cool,數位學習,線上課程', 'url': 'https://cool.ntu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA,Office of International Affairs',
                'location': '禮賢樓（原卓越聯合大樓）7 樓',
                'tel': '02-3366-2007',
                'email': 'oia@ntu.edu.tw',
                'office_hours': '週一至週五 09:00-17:00；國際學生櫃檯 12:00-16:30',
                'url': 'https://oia.ntu.edu.tw/',
            },
            {
                'name': '校長室',
                'aliases': '校長辦公室,President Office',
                # 查無具體大樓，seed_schools 會落到 school.main_tel
            },
            {
                'name': '教務處',
                'aliases': '註冊組,課務組,Office of Academic Affairs',
                'url': 'https://www.aca.ntu.edu.tw/',
                # 官網未列具體大樓樓層
            },
            {
                'name': '學務處（學務長室）',
                'aliases': '學生事務處,生活輔導組,Office of Student Affairs',
                'location': '第一行政大樓 1 樓 114 室',
                'url': 'https://osa.ntu.edu.tw/',
            },
            {
                'name': '總務處',
                'aliases': '事務組,General Affairs',
                'location': '第二行政大樓',
                'url': 'https://ga.ntu.edu.tw/',
            },
            {
                'name': '學生保健中心',
                'aliases': '健康暨心理輔導中心,Student Health Center',
                'url': 'https://shmc.ntu.edu.tw/',
                # 官網僅列校總區地址，未指出獨立大樓名稱
            },
            {
                'name': '學生心理輔導中心',
                'aliases': '諮商中心,心輔中心,Student Counseling Center',
                'location': '研一宿舍旁 望樂樓',
                'tel': '02-3366-2181',
                'url': 'https://scc_osa.ntu.edu.tw/',
            },
        ],
    },

    'NCU': {
        'address': '320317 桃園市中壢區中大路300號',
        'main_tel': '03-4227151',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '03-4227151',
        'intl_office_ext': '57085',
        'website': 'https://www.ncu.edu.tw/',
        'source': 'https://www.ncu.edu.tw/tw/contact/index.php',
        'verified': _V,
        'calendar_url': 'https://pdc.adm.ncu.edu.tw/p/412-1019-1725.php?Lang=zh-tw',
        'links': [
            {'category': 'lms', 'name': '新 ee-class 易課平台',
             'aliases': 'eeclass,ee-class,易課平台,數位學習,線上課程',
             'url': 'https://ncueeclass.ncu.edu.tw/',
             'note': '舊站 eeclass.ncu.edu.tw 自 109-1 學期起已停用，請勿使用舊網址'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '03-4227151',
                'ext': '57085',
                'email': 'lntlAdms@ncu.edu.tw',
            },
            {
                'name': '校長室',
                'tel': '03-4227151',
                'ext': '57000',
                # 亦可撥 03-4254822 專線；官網未列具體大樓
            },
            {
                'name': '教務處',
                'aliases': '註冊組,課務組,招生組',
                'location': '教研大樓（招生組、教務長室、教學發展中心 4 樓；註冊組、課務組 3 樓）',
                'url': 'https://pdc.adm.ncu.edu.tw/',
            },
            {
                'name': '學務處',
                'aliases': '學生事務處,生活輔導組',
                'url': 'https://osa.ncu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'aliases': '事務組',
                'url': 'https://www.oga.ncu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '衛生保健組',
                'aliases': '保健中心,健康中心',
                'location': '中正圖書館 1 樓',
                'url': 'https://health.ncu.edu.tw/',
            },
            {
                'name': '總圖書館',
                'aliases': '圖書館',
                'location': '行政大樓與中正圖書館之間（校門口附近，白色 8 層樓建築）',
                'url': 'https://www.lib.ncu.edu.tw/',
            },
            {
                'name': '諮商中心',
                'aliases': '諮商輔導中心,心輔中心',
                'location': '中正圖書館（舊圖）1 樓',
                'tel': '03-4227151',
                'ext': '57263',
                'url': 'https://love.adm.ncu.edu.tw/',
            },
        ],
    },

    'NCKU': {
        'address': '701 臺南市東區大學路1號',
        'main_tel': '06-2757575',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '06-2757575',
        'intl_office_ext': '50950',
        'intl_office_url': 'https://oia.ncku.edu.tw/',
        'website': 'https://web.ncku.edu.tw/',
        'source': 'https://oia.ncku.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://web.ncku.edu.tw/p/412-1000-6149.php?Lang=zh-tw',
        'links': [
            {'category': 'portal', 'name': '成功入口',
             'aliases': '成功入口,入口網,校務系統,portal', 'url': 'https://i.ncku.edu.tw/'},
            {'category': 'lms', 'name': 'NCKU Moodle 數位學習平台',
             'aliases': 'moodle,數位學習,線上課程', 'url': 'https://moodle.ncku.edu.tw/',
             'note': '帳號密碼與「成功入口」相同，不需另外註冊'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '06-2757575',
                'ext': '50950',
                'url': 'https://oia.ncku.edu.tw/',
            },
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                'aliases': '課務組,推廣教育中心,教學發展中心',
                'location': '雲平大樓西棟 2 樓（處本部、課務組、推廣教育中心）；'
                            '雲平大樓東棟 3 樓（教學發展中心）',
                'url': 'https://acad.ncku.edu.tw/',
            },
            {
                'name': '學務處',
                'aliases': '學生事務處,生活輔導組',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                # 官網未列具體大樓
            },
            {
                'name': '保健中心',
                # 官網未列具體大樓
            },
            {
                'name': '圖書館',
                'tel': '06-2757575',
                'ext': '65760',
                'url': 'https://www.lib.ncku.edu.tw/',
                # 官網僅列大學路一號，與校本部地址相同，未再區分獨立大樓名稱
            },
            {
                'name': '諮商中心',
                'aliases': '諮商輔導組',
                # 官網未列具體大樓
            },
        ],
    },

    'NCCU': {
        'address': '11605 臺北市文山區指南路二段64號',
        'main_tel': '02-2939-3091',
        'intl_office_name': '國際合作事務處',
        'intl_office_tel': '02-2939-3091',
        'intl_office_ext': '62052',
        'intl_office_url': 'https://oic.nccu.edu.tw/',
        'website': 'https://www.nccu.edu.tw/',
        'source': 'https://oic.nccu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://aca.nccu.edu.tw/zh/%E5%B8%B8%E7%94%A8%E9%80%A3%E7%B5%90/%E5%AD%B8%E5%B9%B4%E8%A1%8C%E4%BA%8B%E6%9B%86',
        'links': [
            {'category': 'portal', 'name': 'iNCCU 愛政大',
             'aliases': 'iNCCU,愛政大,入口網,校務資訊系統,portal', 'url': 'https://i.nccu.edu.tw/'},
            {'category': 'lms', 'name': 'NCCU Moodle 數位學習平台',
             'aliases': 'moodle,數位學習,線上課程', 'url': 'https://moodle45.nccu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際合作事務處',
                'aliases': '國際處,國合處,OIC',
                'location': '行政大樓 8 樓',
                'tel': '02-2939-3091',
                'ext': '62052',
                'email': 'oic@nccu.edu.tw',
                'url': 'https://oic.nccu.edu.tw/',
            },
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                'aliases': '註冊組,課務組',
                'url': 'https://aca.nccu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'url': 'https://osa.nccu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'aliases': '事務組',
                'location': '行政大樓 5 樓',
                'url': 'https://nccuga.nccu.edu.tw/',
            },
            {
                'name': '身心健康中心',
                'aliases': '保健中心,健康中心',
                'location': '身心健康中心大樓（指南路二段117號）2 樓',
                'url': 'https://osa.nccu.edu.tw/tw/身心健康中心',
            },
            {
                'name': '心理諮商',
                'aliases': '諮商中心',
                'location': '身心健康中心大樓（指南路二段117號）3 樓',
                'tel': '02-8237-7419',
            },
            {
                'name': '中正圖書館',
                'aliases': '圖書館,總館',
                'url': 'https://www.lib.nccu.edu.tw/',
            },
            {
                'name': '達賢圖書館',
                'aliases': '社資中心',
                'location': '萬壽路（山下校區外）',
                'url': 'https://dhl.lib.nccu.edu.tw/',
            },
        ],
    },

    'NYCU': {
        # 兩校區並存，地址以交大校區（新竹）為主，陽明校區列在單位說明中
        'address': '30010 新竹市大學路1001號（交大校區）',
        'main_tel': '03-5712121',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '03-5712121',
        'intl_office_ext': '50023',
        'intl_office_url': 'https://oia.nycu.edu.tw/',
        'website': 'https://www.nycu.edu.tw/',
        'source': 'https://oia.nycu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://www.nycu.edu.tw/calendar/',
        'links': [
            {'category': 'portal', 'name': '校園單一入口 NYCU Portal',
             'aliases': 'portal,單一入口,校務系統', 'url': 'https://portal.nycu.edu.tw/'},
            {'category': 'lms', 'name': 'E3 數位教學平臺',
             'aliases': 'e3,數位教學,數位學習,線上課程', 'url': 'https://e3.nycu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處（交大校區）',
                'aliases': '國際處,OIA,新竹國際處',
                'location': '新竹市大學路1001號 浩然圖書館 8 樓',
                'tel': '03-5712121',
                'ext': '50023',
                'email': 'oia@nycu.edu.tw',
                'url': 'https://oia.nycu.edu.tw/',
            },
            {
                'name': '國際事務處（陽明校區）',
                'aliases': '陽明國際處,台北國際處',
                'location': '11221 臺北市北投區立農街二段155號 博雅中心 1 樓',
                'tel': '02-2827-5657',
                'email': 'oia@nycu.edu.tw',
                'url': 'https://oia.nycu.edu.tw/',
            },
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                'url': 'https://aa.nycu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'aliases': '事務組,出納組,文書組,保管組,營繕組,校園規劃組',
                'location': '總務長室於浩然圖書資訊中心 8 樓；副總務長室、校園規劃組於工程五館 542 室；'
                            '文書二組、事務二組、出納二組、保管組於大禮堂 2 樓；營繕二組於服務大樓 3 樓',
                'url': 'https://www.ga.nctu.edu.tw/',
            },
            {
                'name': '浩然圖書資訊中心',
                'aliases': '圖書館,交通館',
                'location': '新竹市大學路1001號（交大校區）8 樓為總務長室所在，圖書館主體樓層另見官網',
                'url': 'https://www.lib.nycu.edu.tw/',
            },
            {
                'name': '諮商中心',
                'aliases': '學生輔導中心',
                'location': '學生活動中心',
            },
            {
                'name': '保健中心',
                'aliases': '健康心理中心',
                # 官網未列具體大樓
            },
        ],
    },

    'NTHU': {
        'address': '30013 新竹市光復路二段101號',
        'main_tel': '03-5715131',
        'website': 'https://www.nthu.edu.tw/',
        'source': 'https://www.nthu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://dgaa.site.nthu.edu.tw/p/407-1209-629-1.php?Lang=zh-tw',
        'links': [
            {'category': 'lms', 'name': 'eeclass 數位學習平台',
             'aliases': 'eeclass,ee-class,數位學習,線上課程', 'url': 'https://eeclass.nthu.edu.tw/',
             'note': '以校務資訊系統帳號登入'},
        ],
        # 國際處分機未在官網查到，刻意留空，不填猜測值
        'units': [
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                'url': 'https://academic.site.nthu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'url': 'https://student.site.nthu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'aliases': '事務組,出納組,文書組,保管組,採購組,校園規劃組,營繕組',
                'location': '校本部行政大樓／第一綜合大樓（1 樓文書組、出納組；2 樓副總務長室、保管組、'
                            '事務組、採購組；3 樓總務長室、校園規劃組；4 樓營繕組）',
                'url': 'https://general.site.nthu.edu.tw/',
            },
            {
                'name': '保健中心',
                # 官網未列具體大樓
            },
            {
                'name': '圖書館',
                # 官網未列具體大樓
            },
            {
                'name': '諮商中心',
                'aliases': '學生輔導中心',
                # 官網未列具體大樓
            },
        ],
    },

    'NCHU': {
        'address': '40227 臺中市南區興大路145號',
        'main_tel': '04-2287-3181',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '04-2284-0206',
        'intl_office_url': 'https://oia.nchu.edu.tw/',
        'website': 'https://www.nchu.edu.tw/',
        'source': 'https://oia.nchu.edu.tw/index.php/zh/1-1-about-tw/1-1-6-contact-tw',
        'verified': _V,
        'calendar_url': 'https://www.nchu.edu.tw/about/mid/487',
        'links': [
            {'category': 'portal', 'name': 'NCHU Portal 校務系統',
             'aliases': 'portal,入口網,校務系統', 'url': 'https://portal.nchu.edu.tw/'},
            {'category': 'lms', 'name': 'iLearning 3.0 教學平台',
             'aliases': 'ilearning,數位學習,線上課程', 'url': 'https://lms2020.nchu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 3 樓',
                'tel': '04-2284-0206',
                'email': 'oia@nchu.edu.tw',
                'url': 'https://oia.nchu.edu.tw/',
            },
            {
                'name': '校長室',
                'url': 'https://www.nchu.edu.tw/administrative/mid/982',
                # 官網未列具體大樓，僅有分機數字，不確定是否等同房號，不採信
            },
            {
                'name': '教務處',
                'location': '行政大樓 3 樓',
                'url': 'https://oaa.nchu.edu.tw/',
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'location': '行政大樓 3 樓（主要業務單位；部分組別另設於惠蓀堂、雲平樓、興大二村南棟）',
                'url': 'https://www.nchu.edu.tw/administrative/mid/278',
            },
            {
                'name': '總務處',
                'aliases': '事務組,採購組,出納組,營繕組',
                'location': '行政大樓 3 樓（總務長室主要業務單位；事務組、採購組 1 樓；出納組、營繕組 2 樓）',
                'url': 'https://oga.nchu.edu.tw/',
            },
            {
                'name': '健康及諮商中心',
                'aliases': '保健中心,諮商中心',
                'location': '惠蓀堂 1 樓、4 樓',
                'url': 'https://www.osa.nchu.edu.tw/osa/hac/',
            },
            {
                'name': '圖書館',
                'url': 'https://www.lib.nchu.edu.tw/',
                # 官網未列具體大樓（圖書館本身即為獨立館舍，但未查到明確描述）
            },
        ],
    },

    'NSYSU': {
        'address': '804 高雄市鼓山區蓮海路70號',
        'main_tel': '07-5252000',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '07-5252000',
        'intl_office_ext': '2244',
        'intl_office_url': 'https://oia.nsysu.edu.tw/',
        'website': 'https://www.nsysu.edu.tw/',
        'source': 'https://oia.nsysu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://oaa.nsysu.edu.tw/p/412-1003-98.php?Lang=zh-tw',
        'links': [
            {'category': 'lms', 'name': '中山網路大學',
             'aliases': '網路大學,cu,數位學習,線上課程', 'url': 'https://cu.nsysu.edu.tw/'},
            {'category': 'course', 'name': '選課系統',
             'aliases': '選課,加退選,selcrs', 'url': 'https://selcrs.nsysu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 1 樓 1006 室',
                'tel': '07-5252000',
                'ext': '2244',
                'url': 'https://oia.nsysu.edu.tw/',
            },
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                'url': 'https://oaa.nsysu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'tel': '07-5252000',
                'ext': '2201',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'aliases': '文書組,事務組,出納組,保管組,營繕組,駐警隊',
                'location': '行政大樓（總務處主要業務單位 4 樓；出納組、行政支援 3 樓；駐警隊、值班室 1 樓）',
                'url': 'https://rpa48.nsysu.edu.tw/',
            },
            {
                'name': '保健中心',
                'aliases': '諮商中心',
                # 官網未列具體大樓
            },
            {
                'name': '圖書館',
                'aliases': '圖書與資訊處',
                'url': 'https://lis.nsysu.edu.tw/',
                # 官網未列具體大樓
            },
        ],
    },

    'NTNU': {
        'address': '106209 臺北市大安區和平東路一段162號',
        'main_tel': '02-7749-1111',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '02-7749-1272',
        'intl_office_url': 'https://oia.ntnu.edu.tw/',
        'website': 'https://www.ntnu.edu.tw/',
        'source': 'https://www.ntnu.edu.tw/static.php?id=contactus',
        'verified': _V,
        'links': [
            {'category': 'lms', 'name': 'NTNU Moodle 數位學習平台',
             'aliases': 'moodle,數位學習,線上課程', 'url': 'https://moodle3.ntnu.edu.tw/',
             'note': '舊站 moodle2.ntnu.edu.tw 已無法連線，請用此網址'},
            {'category': 'portal', 'name': '校務行政帳號啟用',
             'aliases': '帳號啟用,新生帳號,開通', 'url': 'https://ap.itc.ntnu.edu.tw/nipinit/',
             'note': '新生必須先在此啟用帳號，才能使用其他校內系統'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '02-7749-1272',
                'url': 'https://oia.ntnu.edu.tw/',
            },
            {
                'name': '校長室',
                # 官網未列具體大樓
            },
            {
                'name': '教務處',
                # 官網未列具體大樓
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                # 官網未列具體大樓
            },
            {
                'name': '總務處',
                'url': 'https://www.ga.ntnu.edu.tw/',
                # 官網未列具體大樓
            },
            {
                'name': '健康中心',
                'aliases': '保健中心',
                # 官網未列具體大樓
            },
            {
                'name': '圖書館',
                'aliases': '圖書館校區',
                'location': '和平校區Ⅱ（圖書館校區），臺北市大安區和平東路一段129號',
                'url': 'https://www.lib.ntnu.edu.tw/',
            },
            {
                'name': '學生輔導中心',
                'aliases': '諮商中心',
                # 官網未列具體大樓
            },
        ],
    },

    'NTPU': {
        'address': '23741 新北市三峽區大學路151號',
        'main_tel': '02-8674-1111',
        'intl_office_name': '國際事務處',
        'intl_office_url': 'http://oia.ntpu.edu.tw/',
        'website': 'https://www.ntpu.edu.tw/',
        'source': 'http://oia.ntpu.edu.tw/',
        'verified': _V,
        # 國際處分機未查到，留空
        'units': [
            {'name': '國際事務處', 'aliases': '國際處,OIA', 'url': 'http://oia.ntpu.edu.tw/'},
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NDHU': {
        'address': '974301 花蓮縣壽豐鄉大學路二段1號',
        'main_tel': '03-8635000',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '03-8905107',
        'intl_office_url': 'https://oia.ndhu.edu.tw/',
        'website': 'https://www.ndhu.edu.tw/',
        'source': 'https://www.ndhu.edu.tw/p/412-1000-8813.php?Lang=zh-tw',
        'verified': _V,
        'calendar_url': 'https://sys.ndhu.edu.tw/AA/calendar/',
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '03-8905107',
                'url': 'https://oia.ndhu.edu.tw/',
            },
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://aa.ndhu.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處', 'url': 'https://ga.ndhu.edu.tw/'},
            {'name': '圖書資訊處', 'aliases': '圖書館'},
            {'name': '心理諮商輔導中心', 'aliases': '諮商中心,保健中心'},
        ],
    },

    'NCNU': {
        'address': '545301 南投縣埔里鎮大學路1號',
        'main_tel': '049-2910960',
        'website': 'https://www.ncnu.edu.tw/',
        'source': 'https://www.doc.ncnu.edu.tw/ncnu/index.php/',
        'verified': _V,
        'links': [
            {'category': 'lms', 'name': '課程資訊網 Moodle',
             'aliases': 'moodle,數位學習,課程資訊網,線上課程', 'url': 'https://moodle.ncnu.edu.tw/'},
        ],
        # 校內分機查詢系統：https://ccweb.ncnu.edu.tw/telquery/
        'units': [
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://aca.ncnu.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處', 'url': 'https://general.ncnu.edu.tw/'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NIU': {
        'address': '260007 宜蘭縣宜蘭市神農路一段1號',
        'main_tel': '03-935-7400',
        'website': 'https://www.niu.edu.tw/',
        'source': 'https://www.niu.edu.tw/p/412-1000-1052.php',
        'verified': _V,
        'calendar_url': 'https://academic.niu.edu.tw/p/412-1003-5555.php',
        'links': [
            {'category': 'portal', 'name': '校務資訊服務入口網',
             'aliases': '單一登入,SSO,校務系統,portal', 'url': 'https://ccsys.niu.edu.tw/SSO/'},
            {'category': 'course', 'name': '教務行政資訊系統',
             'aliases': '教務系統,選課,成績', 'url': 'https://acade.niu.edu.tw/'},
        ],
        'units': [
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://academic.niu.edu.tw/'},
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'location': '體育館 2、3 樓',
                'url': 'https://niuosa.niu.edu.tw/',
            },
            {'name': '總務處'},
            {'name': '圖書資訊館', 'aliases': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NUU': {
        'address': '36003 苗栗市恭敬里聯大一號（二坪山校區）',
        'main_tel': '037-381000',
        'intl_office_name': '研究發展處 國際及兩岸事務組',
        'intl_office_tel': '037-381403',
        'intl_office_url': 'https://oia.nuu.edu.tw/',
        'website': 'https://www.nuu.edu.tw/',
        'source': 'https://www.nuu.edu.tw/p/412-1000-3769.php?Lang=zh-tw',
        'verified': _V,
        'calendar_url': 'https://curr.nuu.edu.tw/p/404-1076-6482.php',
        'links': [
            {'category': 'lms', 'name': '聯合數位學園',
             'aliases': 'elearning,數位學習,線上課程', 'url': 'https://elearning.nuu.edu.tw/'},
            {'category': 'portal', 'name': '校務資訊系統',
             'aliases': '校務系統,portal,選課,成績', 'url': 'https://eap10.nuu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際及兩岸事務組',
                'aliases': '國際處,國際組,OIA',
                'tel': '037-381403',
                'url': 'https://oia.nuu.edu.tw/',
                'office_hours': '另有 037-381407、037-381408 兩線',
            },
            {'name': '校長室'},
            {
                'name': '教務處',
                'aliases': '課務組,註冊組,綜合業務組,教學發展中心',
                'location': '八甲校區 通識教育中心大樓後棟 2 樓',
                'url': 'https://aca.nuu.edu.tw/',
            },
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NCYU': {
        'address': '600355 嘉義市東區學府路300號（蘭潭校區，校本部）',
        'main_tel': '05-2717000',
        'website': 'https://www.ncyu.edu.tw/',
        'source': 'https://www.ncyu.edu.tw/affair/ServerFile/Get/cba1d4d6-6943-4fb0-9615-aa6afd1e6bb1?nodeId=39496&sId=128494',
        'verified': _V,
        'calendar_url': 'https://website.ncyu.edu.tw/academic/Subject?nodeId=10496',
        # 蘭潭、民雄、林森、新民四校區，地址以校本部蘭潭校區為準
        'units': [
            {
                'name': '校長室',
                'tel': '05-2717100',
                'location': '蘭潭校區 中正樓行政中心',
            },
            {
                'name': '教務處',
                'tel': '05-2717020',
                'location': '蘭潭校區 中正樓行政中心',
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'tel': '05-2717054',
                'location': '蘭潭校區 中正樓行政中心',
            },
            {
                'name': '總務處',
                'tel': '05-2717177',
                'location': '蘭潭校區 中正樓行政中心',
            },
            {
                'name': '圖書資訊館',
                'aliases': '圖書館',
                'location': '蘭潭校區 圖書資訊館',
            },
            {
                'name': '保健中心',
                'aliases': '諮商中心',
                # 官網未列具體大樓
            },
        ],
    },

    'NQU': {
        'address': '892 金門縣金寧鄉大學路1號',
        'main_tel': '082-313300',
        'website': 'https://www.nqu.edu.tw/',
        'source': 'https://www.nqu.edu.tw/',
        'verified': _V,
        'units': [
            {'name': '副校長室'},
            {'name': '教務處', 'url': 'https://teach.nqu.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    # 以下學校已確認地址，但總機號碼只在「帶著猜測號碼去搜尋」時被回音確認，
    # 未在官方頁面上獨立看到，因此刻意不寫入電話，只留地址。
    'NUTN': {
        'address': '700301 臺南市中西區樹林街二段33號（府城校區）',
        'website': 'https://www.nutn.edu.tw/',
        'source': 'https://academic.nutn.edu.tw/',
        'verified': _V,
        'units': [
            {
                'name': '教務處',
                'aliases': '教學組,學籍組,規劃組,推廣組,數位學習中心,教學發展中心',
                'url': 'https://academic.nutn.edu.tw/',
                # 官網列出各組分機號碼，但未標明具體樓層，不確定格式是否等同對外可撥分機，不採信
            },
            {'name': '校長室'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館', 'aliases': '圖書館與資訊服務組'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTTU': {
        'address': '950309 臺東縣臺東市大學路二段369號',
        'website': 'https://www.nttu.edu.tw/',
        'source': 'https://www.nttu.edu.tw/',
        'verified': _V,
        'units': [
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書資訊館', 'aliases': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTUT': {
        'address': '10608 臺北市大安區忠孝東路三段1號',
        # 與既有 SCHOOL_CRISIS_PHONES 的 NTUT 總機 0227712171 相互印證
        'main_tel': '02-2771-2171',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '02-2771-2171',
        'intl_office_ext': '6500',
        'intl_office_url': 'https://oia.ntut.edu.tw/',
        'website': 'https://www.ntut.edu.tw/',
        'source': 'https://oia.ntut.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://oaa.ntut.edu.tw/p/412-1008-12781.php?Lang=zh-tw',
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '第二教學大樓 1 樓',
                'tel': '02-2771-2171',
                'ext': '6500',
                'email': 'intstudy@ntut.edu.tw',
                'url': 'https://oia.ntut.edu.tw/',
            },
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://aa.ntut.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            # 官網校園地圖僅描述「校園左側區塊，鄰近行政大樓」，不夠精確到可定位，不採信
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTUST': {
        'address': '10607 臺北市大安區基隆路四段43號',
        'intl_office_name': '國際事務處',
        'intl_office_url': 'https://www.oia.ntust.edu.tw/',
        'website': 'https://www.ntust.edu.tw/',
        'source': 'https://www.ntust.edu.tw/p/404-1000-88778.php?Lang=zh-tw',
        'verified': _V,
        'calendar_url': 'https://www.academic.ntust.edu.tw/p/404-1048-78935.php?Lang=zh-tw',
        'links': [
            {'category': 'lms', 'name': 'Moodle 教學平台',
             'aliases': 'moodle,數位學習,線上課程', 'url': 'https://moodle2.ntust.edu.tw/',
             'note': '舊站 moodle.ntust.edu.tw 已無法連線，請用此網址；帳號與校務資訊系統整合'},
        ],
        # 官網列出的是各承辦人的直撥號碼，無法判斷哪一支是對外總線，故不填電話
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '第 4 棟 IB 國際大樓',
                'email': 'oia@mail.ntust.edu.tw',
                'url': 'https://www.oia.ntust.edu.tw/',
            },
            {
                'name': '校長室',
                'aliases': '副校長室',
                'location': '第 1 棟行政大樓',
                # 校內配置圖僅列「副校長室」，校長室本身樓層未單獨標示
            },
            {
                'name': '教務處',
                'location': '第 1 棟行政大樓（教務處綜合業務組另設於第 4 棟 IB 國際大樓）',
                'url': 'https://www.ntust.edu.tw/p/412-1000-106.php?Lang=zh-tw',
            },
            {
                'name': '學務處',
                'aliases': '學生事務處',
                'location': '第 2 棟學生活動中心',
            },
            {
                'name': '總務處',
                'aliases': '保管組,檔案室',
                'location': '第 1 棟行政大樓（保管組、檔案室另設於第 5 棟 T3 第三教學大樓）',
            },
            {
                'name': '衛生保健組',
                'aliases': '健康中心,保健中心',
                'location': '第 3 棟體育館',
            },
            {'name': '圖書館'},
            {'name': '諮商中心', 'aliases': '學生輔導中心'},
        ],
    },

    'NPTU': {
        'address': '900392 屏東縣屏東市民生東路51號',
        'main_tel': '08-7663800',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '08-7663800',
        'intl_office_url': 'https://oia.nptu.edu.tw/',
        'website': 'https://www.nptu.edu.tw/',
        'source': 'https://oia.nptu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://cud.nptu.edu.tw/p/412-1065-4687.php?Lang=zh-tw',
        'links': [
            {'category': 'lms', 'name': '數位學習平台',
             'aliases': 'elearning,數位學習,線上課程', 'url': 'https://elearning.nptu.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 3 樓',
                'tel': '08-7663800',
                'email': 'oia@mail.nptu.edu.tw',
                'url': 'https://oia.nptu.edu.tw/',
            },
        ],
    },

    'NTCUST': {
        'address': '404336 臺中市北區三民路三段129號',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '04-2219-5764',
        'intl_office_url': 'https://oia.nutc.edu.tw/',
        'website': 'https://www.nutc.edu.tw/',
        'source': 'https://oia.nutc.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://aca.nutc.edu.tw/p/412-1015-4596.php',
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '中科大樓 1 樓',
                'tel': '04-2219-5764',
                'url': 'https://oia.nutc.edu.tw/',
            },
            {'name': '校長室', 'url': 'https://www.nutc.edu.tw/p/412-1000-99.php'},
            {'name': '教務處', 'url': 'https://academic.nutc.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {
                'name': '圖書館',
                'aliases': '三民總館,民生分館',
                'location': '三民校區 中商大樓 1 樓（另有民生校區 綜合大樓 3 樓 民生分館）',
                'url': 'https://elib.nutc.edu.tw/',
            },
            {'name': '職涯及諮商輔導中心', 'aliases': '保健中心,諮商中心'},
        ],
    },

    'NKUST': {
        'intl_office_name': '國際事務處',
        'intl_office_url': 'https://oia.nkust.edu.tw/',
        'website': 'https://www.nkust.edu.tw/',
        'source': 'https://oia.nkust.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://www.nkust.edu.tw/p/404-1000-4622.php',
        'links': [
            {'category': 'portal', 'name': '校務系統',
             'aliases': 'webap,校務行政,portal,選課', 'url': 'https://webap.nkust.edu.tw/nkust/'},
        ],
        # 多校區（建工、燕巢、第一、楠梓、旗津），官網國際處頁未列地址與電話，
        # 僅取得信箱；地址與總機待補
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'email': 'nkustoia@nkust.edu.tw',
                'url': 'https://oia.nkust.edu.tw/',
            },
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://acad.nkust.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
            # 多校區，分機第一碼代表校區（1＝建工/燕巢），詳細位置請洽總機轉接
        ],
    },

    'YunTech': {
        'address': '640301 雲林縣斗六市大學路三段123號',
        'main_tel': '05-534-2601',
        'website': 'https://www.yuntech.edu.tw/',
        'source': 'https://www.yuntech.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://aax.yuntech.edu.tw/index.php/ql-ct/calendar',
        'links': [
            {'category': 'course', 'name': '選課系統',
             'aliases': '選課,加退選', 'url': 'https://webapp.yuntech.edu.tw/aaxccs/'},
        ],
        'units': [
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://aax.yuntech.edu.tw/'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {
                'name': '總務處',
                'location': '圖書館 1-2 樓（部分業務）、圖書館 4 樓（部分業務）',
                'url': 'https://ags.yuntech.edu.tw/',
            },
            {'name': '圖書資訊處', 'aliases': '圖書館', 'url': 'https://www.yuntech.edu.tw/index.php/2019-07-25-11-32-12/2019-04-10-08-05-51/2019-04-23-06-06-12'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NPUST': {
        'address': '屏東縣內埔鄉學府路1號',
        'main_tel': '08-7703202',
        'intl_office_name': '國際事務處',
        'intl_office_tel': '08-7740561',
        'intl_office_url': 'https://oia2.npust.edu.tw/',
        'website': 'https://www.npust.edu.tw/',
        'source': 'https://oia2.npust.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://aa.npust.edu.tw/calendar/calendar.html',
        'links': [
            {'category': 'lms', 'name': '數位學習入口',
             'aliases': 'moodle,elearning,數位學習,線上課程', 'url': 'https://elearning.npust.edu.tw/'},
            {'category': 'portal', 'name': '校務行政系統',
             'aliases': '校務系統,選課,course', 'url': 'https://course.npust.edu.tw/'},
        ],
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 4 樓',
                'tel': '08-7740561',
                'email': 'oia@mail.npust.edu.tw',
                'office_hours': '08:30-12:30、13:30-17:30',
                'url': 'https://oia2.npust.edu.tw/',
            },
            {'name': '校長室'},
            {'name': '教務處', 'url': 'https://aa.npust.edu.tw/'},
            {'name': '學生事務處', 'aliases': '學務處,學生諮商中心,諮商中心'},
            {'name': '總務處'},
            {'name': '圖書與會展館', 'aliases': '圖書館'},
            {'name': '保健中心'},
        ],
    },

    'NKUHT': {
        'address': '81271 高雄市小港區松和路1號',
        'main_tel': '07-806-0505',
        'website': 'https://www.nkuht.edu.tw/',
        'source': 'https://www.nkuht.edu.tw/',
        'verified': _V,
        'units': [
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書資訊大樓', 'aliases': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NFU': {
        'address': '632301 雲林縣虎尾鎮文化路64號',
        'main_tel': '05-631-5000',
        'website': 'https://www.nfu.edu.tw/',
        'source': 'https://www.nfu.edu.tw/zh/administration',
        'verified': _V,
        'calendar_url': 'https://www.nfu.edu.tw/zh/nfu-calendar',
        'units': [
            {'name': '校長室', 'tel': '05-631-5011'},
            {'name': '教務處', 'tel': '05-631-5101'},
            {
                'name': '學生事務處',
                'aliases': '學務處,衛生保健,諮商輔導,軍訓室,課外活動,生活輔導',
                'tel': '05-631-5137',
            },
            {'name': '總務處', 'tel': '05-631-5202'},
            {'name': '圖書館'},
        ],
    },

    'NPU': {
        'address': '880011 澎湖縣馬公市六合路300號',
        'main_tel': '06-926-4115',
        'website': 'https://www.npu.edu.tw/',
        'source': 'https://www.npu.edu.tw/',
        'verified': _V,
        'units': [
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NKNU': {
        'address': '802561 高雄市苓雅區和平一路116號（和平校區）',
        'main_tel': '07-717-2930',
        'website': 'https://w3.nknu.edu.tw/',
        'source': 'https://w3.nknu.edu.tw/zh/contact',
        'verified': _V,
        'units': [
            {
                'name': '燕巢校區',
                'aliases': '燕巢,第二校區',
                'location': '824004 高雄市燕巢區深中路62號',
            },
            {'name': '教務長室', 'tel': '07-717-2930', 'ext': '1101'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {
                'name': '總務處',
                'aliases': '文書組,事務組,保管組,出納組,營繕組',
                'tel': '07-717-2930',
                'ext': '1311',
            },
            {
                'name': '衛生保健組',
                'aliases': '保健中心,諮商中心',
                'tel': '07-717-2930',
                'ext': '1291',
            },
            {
                'name': '和平圖書館',
                'aliases': '愛閱館,圖書館',
                'tel': '07-717-2930',
                'ext': '1414',
            },
        ],
    },

    'NCUE': {
        'address': '500207 彰化市進德路一號（進德校區）',
        'main_tel': '04-723-2105',
        'website': 'https://www.ncue.edu.tw/',
        'source': 'https://www.ncue.edu.tw/',
        'verified': _V,
        'units': [
            {
                'name': '師大路校區',
                'aliases': '寶山校區,第二校區',
                'location': '500208 彰化市師大路2號',
            },
            {'name': '校長室', 'tel': '04-723-2105', 'ext': '1040'},
            {'name': '教務處', 'tel': '04-723-2105', 'ext': '5603'},
            {'name': '學生事務處', 'aliases': '學務處', 'tel': '04-723-2105', 'ext': '5703'},
            {'name': '總務處', 'tel': '04-723-2105', 'ext': '5803'},
            {'name': '圖書館', 'aliases': '圖書館電算中心'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTUE': {
        'address': '10671 臺北市大安區和平東路二段134號',
        'main_tel': '02-2732-1104',
        'website': 'https://www.ntue.edu.tw/',
        'source': 'https://www.ntue.edu.tw/p/404-1000-12835.php?Lang=zh-tw',
        'verified': _V,
        'units': [
            {
                'name': '校長室',
                'aliases': '副校長室,秘書室,人事室,主計室,研發處',
                'location': '行政大樓（代號 A）',
            },
            {'name': '教務處', 'location': '行政大樓（代號 A）'},
            {'name': '學務處', 'aliases': '學生事務處', 'location': '行政大樓（代號 A）'},
            {'name': '總務處', 'location': '行政大樓（代號 A）'},
            {'name': '圖書館', 'location': '與行政大樓（代號 A）相連'},
            {
                'name': '諮商組',
                'aliases': '諮商中心,學生輔導中心',
                'location': '至善樓（代號 G）',
            },
            {'name': '保健中心'},
        ],
    },

    'NTCU': {
        'address': '403514 臺中市西區民生路140號（民生校區）',
        'main_tel': '04-2218-3199',
        'website': 'https://www.ntcu.edu.tw/',
        'source': 'https://www.ntcu.edu.tw/',
        'verified': _V,
        'calendar_url': 'https://oaa.ntcu.edu.tw/redirect.php?ID=Calendar',
        'units': [
            {
                'name': '英才校區',
                'aliases': '第二校區',
                'location': '403012 臺中市西區民生路227號',
                'tel': '04-2218-8050',
            },
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處', 'url': 'https://oga.ntcu.edu.tw/'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTUS': {
        'address': '404401 臺中市北區雙十路一段16號',
        'main_tel': '04-2221-3108',
        'website': 'https://www.ntus.edu.tw/',
        'source': 'https://www.ntus.edu.tw/',
        'verified': _V,
        'units': [
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NTUB': {
        'address': '100025 臺北市中正區濟南路一段321號（臺北校區）',
        'main_tel': '02-3322-2777',
        'website': 'https://www.ntub.edu.tw/',
        'source': 'https://www.ntub.edu.tw/',
        'verified': _V,
        'units': [
            {
                'name': '桃園校區',
                'aliases': '平鎮校區,第二校區',
                'location': '324022 桃園市平鎮區福龍路一段100號',
                'tel': '03-4506333',
            },
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
            {'name': '保健中心', 'aliases': '諮商中心'},
        ],
    },

    'NOU': {
        'address': '247 新北市蘆洲區中正路172號',
        'main_tel': '02-2282-9355',
        'website': 'https://www.nou.edu.tw/',
        'source': 'https://www.nou.edu.tw/',
        'verified': _V,
        # 空中大學為遠距教學，另有各地學習指導中心
        'units': [
            {'name': '校長室'},
            {'name': '教務處'},
            {'name': '學務處', 'aliases': '學生事務處'},
            {'name': '總務處'},
            {'name': '圖書館'},
        ],
    },
}
