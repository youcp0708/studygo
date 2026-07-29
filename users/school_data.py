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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '03-4227151',
                'ext': '57085',
                'email': 'lntlAdms@ncu.edu.tw',
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '06-2757575',
                'ext': '50950',
                'url': 'https://oia.ncku.edu.tw/',
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
        ],
    },

    'NTHU': {
        'address': '30013 新竹市光復路二段101號',
        'main_tel': '03-5715131',
        'website': 'https://www.nthu.edu.tw/',
        'source': 'https://www.nthu.edu.tw/',
        'verified': _V,
        # 國際處分機未在官網查到，刻意留空，不填猜測值
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 3 樓',
                'tel': '04-2284-0206',
                'email': 'oia@nchu.edu.tw',
                'url': 'https://oia.nchu.edu.tw/',
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '行政大樓 1 樓 1006 室',
                'tel': '07-5252000',
                'ext': '2244',
                'url': 'https://oia.nsysu.edu.tw/',
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '02-7749-1272',
                'url': 'https://oia.ntnu.edu.tw/',
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'tel': '03-8905107',
                'url': 'https://oia.ndhu.edu.tw/',
            },
        ],
    },

    'NCNU': {
        'address': '545301 南投縣埔里鎮大學路1號',
        'main_tel': '049-2910960',
        'website': 'https://www.ncnu.edu.tw/',
        'source': 'https://www.doc.ncnu.edu.tw/ncnu/index.php/',
        'verified': _V,
        # 校內分機查詢系統：https://ccweb.ncnu.edu.tw/telquery/
    },

    'NIU': {
        'address': '260007 宜蘭縣宜蘭市神農路一段1號',
        'main_tel': '03-935-7400',
        'website': 'https://www.niu.edu.tw/',
        'source': 'https://www.niu.edu.tw/p/412-1000-1052.php',
        'verified': _V,
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
        'units': [
            {
                'name': '國際及兩岸事務組',
                'aliases': '國際處,國際組,OIA',
                'tel': '037-381403',
                'url': 'https://oia.nuu.edu.tw/',
                'office_hours': '另有 037-381407、037-381408 兩線',
            },
        ],
    },

    'NCYU': {
        'address': '600355 嘉義市東區學府路300號（蘭潭校區，校本部）',
        'main_tel': '05-2717000',
        'website': 'https://www.ncyu.edu.tw/',
        'source': 'https://www.ncyu.edu.tw/',
        'verified': _V,
        # 蘭潭、民雄、林森、新民四校區，地址以校本部蘭潭校區為準
    },

    'NQU': {
        'address': '892 金門縣金寧鄉大學路1號',
        'main_tel': '082-313300',
        'website': 'https://www.nqu.edu.tw/',
        'source': 'https://www.nqu.edu.tw/',
        'verified': _V,
    },

    # 以下學校已確認地址，但總機號碼只在「帶著猜測號碼去搜尋」時被回音確認，
    # 未在官方頁面上獨立看到，因此刻意不寫入電話，只留地址。
    'NUTN': {
        'address': '700301 臺南市中西區樹林街二段33號（府城校區）',
        'website': 'https://www.nutn.edu.tw/',
        'source': 'https://www.nutn.edu.tw/about.html',
        'verified': _V,
    },

    'NTTU': {
        'address': '950309 臺東縣臺東市大學路二段369號',
        'website': 'https://www.nttu.edu.tw/',
        'source': 'https://www.nttu.edu.tw/',
        'verified': _V,
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
        ],
    },

    'NTUST': {
        'address': '10607 臺北市大安區基隆路四段43號',
        'intl_office_name': '國際事務處',
        'intl_office_url': 'https://www.oia.ntust.edu.tw/',
        'website': 'https://www.ntust.edu.tw/',
        'source': 'https://www.oia.ntust.edu.tw/p/404-1060-60572.php?Lang=zh-tw',
        'verified': _V,
        # 官網列出的是各承辦人的直撥號碼，無法判斷哪一支是對外總線，故不填電話
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '國際大樓 4 樓 402 室',
                'email': 'oia@mail.ntust.edu.tw',
                'url': 'https://www.oia.ntust.edu.tw/',
            },
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
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'location': '中科大樓 1 樓',
                'tel': '04-2219-5764',
                'url': 'https://oia.nutc.edu.tw/',
            },
        ],
    },

    'NKUST': {
        'intl_office_name': '國際事務處',
        'intl_office_url': 'https://oia.nkust.edu.tw/',
        'website': 'https://www.nkust.edu.tw/',
        'source': 'https://oia.nkust.edu.tw/',
        'verified': _V,
        # 多校區（建工、燕巢、第一、楠梓、旗津），官網國際處頁未列地址與電話，
        # 僅取得信箱；地址與總機待補
        'units': [
            {
                'name': '國際事務處',
                'aliases': '國際處,OIA',
                'email': 'nkustoia@nkust.edu.tw',
                'url': 'https://oia.nkust.edu.tw/',
            },
        ],
    },

    'YunTech': {
        'address': '640301 雲林縣斗六市大學路三段123號',
        'main_tel': '05-534-2601',
        'website': 'https://www.yuntech.edu.tw/',
        'source': 'https://www.yuntech.edu.tw/',
        'verified': _V,
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
        ],
    },

    'NKUHT': {
        'address': '81271 高雄市小港區松和路1號',
        'main_tel': '07-806-0505',
        'website': 'https://www.nkuht.edu.tw/',
        'source': 'https://www.nkuht.edu.tw/',
        'verified': _V,
    },

    'NFU': {
        'address': '632301 雲林縣虎尾鎮文化路64號',
        'main_tel': '05-631-5000',
        'website': 'https://www.nfu.edu.tw/',
        'source': 'https://www.nfu.edu.tw/',
        'verified': _V,
    },

    'NPU': {
        'address': '880011 澎湖縣馬公市六合路300號',
        'main_tel': '06-926-4115',
        'website': 'https://www.npu.edu.tw/',
        'source': 'https://www.npu.edu.tw/',
        'verified': _V,
    },

    'NKNU': {
        'address': '802561 高雄市苓雅區和平一路116號（和平校區）',
        'main_tel': '07-717-2930',
        'website': 'https://w3.nknu.edu.tw/',
        'source': 'https://w3.nknu.edu.tw/zh/',
        'verified': _V,
        'units': [
            {
                'name': '燕巢校區',
                'aliases': '燕巢,第二校區',
                'location': '824004 高雄市燕巢區深中路62號',
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
        ],
    },

    'NTUE': {
        'address': '10671 臺北市大安區和平東路二段134號',
        'main_tel': '02-2732-1104',
        'website': 'https://www.ntue.edu.tw/',
        'source': 'https://www.ntue.edu.tw/p/412-1000-85.php?Lang=zh-tw',
        'verified': _V,
    },

    'NTCU': {
        'address': '403514 臺中市西區民生路140號（民生校區）',
        'main_tel': '04-2218-3199',
        'website': 'https://www.ntcu.edu.tw/',
        'source': 'https://www.ntcu.edu.tw/',
        'verified': _V,
        'units': [
            {
                'name': '英才校區',
                'aliases': '第二校區',
                'location': '403012 臺中市西區民生路227號',
                'tel': '04-2218-8050',
            },
        ],
    },

    'NTUS': {
        'address': '404401 臺中市北區雙十路一段16號',
        'main_tel': '04-2221-3108',
        'website': 'https://www.ntus.edu.tw/',
        'source': 'https://www.ntus.edu.tw/',
        'verified': _V,
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
        ],
    },

    'NOU': {
        'address': '247 新北市蘆洲區中正路172號',
        'main_tel': '02-2282-9355',
        'website': 'https://www.nou.edu.tw/',
        'source': 'https://www.nou.edu.tw/',
        'verified': _V,
        # 空中大學為遠距教學，另有各地學習指導中心
    },
}
