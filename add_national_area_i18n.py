import polib

new_strings = {
    '各國專區': {
        'en': 'National Area',
        'id': 'Area Nasional',
        'ja': '国別専用ページ',
        'ms': 'Kawasan Negara',
        'my': 'နိုင်ငံဒေသများ',
        'th': 'พื้นที่แต่ละประเทศ',
    },
    '各地區申請資訊': {
        'en': 'Application Info by Region',
        'id': 'Info Pendaftaran per Wilayah',
        'ja': '地域別申請情報',
        'ms': 'Maklumat Permohonan Mengikut Kawasan',
        'my': 'ဒေသအလိုက် လျှောက်ထားမှု သတင်းအချက်အလက်',
        'th': 'ข้อมูลการสมัครตามภูมิภาค',
    },
    '依所在地選擇對應的申請說明，直接連結至海外聯招會官方網站。': {
        'en': 'Select your region to view the relevant application guide, linked directly to the official overseas admissions site.',
        'id': 'Pilih wilayah Anda untuk melihat panduan pendaftaran yang sesuai, terhubung langsung ke situs resmi.',
        'ja': '所在地を選択して該当する申請説明を確認してください。公式サイトへ直接リンクします。',
        'ms': 'Pilih kawasan anda untuk melihat panduan permohonan yang berkaitan, pautan terus ke laman web rasmi.',
        'my': 'သင်၏တည်နေရာကို ရွေးချယ်ပြီး ကိုက်ညီသောလျှောက်ထားမှုလမ်းညွှန်ကို ကြည့်ပါ။',
        'th': 'เลือกภูมิภาคของคุณเพื่อดูคำแนะนำการสมัคร เชื่อมต่อโดยตรงไปยังเว็บไซต์ทางการ',
    },
    '以下連結將跳轉至': {
        'en': 'The links below will redirect you to the ',
        'id': 'Tautan berikut akan mengarahkan ke ',
        'ja': '以下のリンクは',
        'ms': 'Pautan berikut akan mengarahkan ke ',
        'my': 'အောက်ပါ လင့်ခ်များသည် ',
        'th': 'ลิงก์ด้านล่างจะนำคุณไปยัง ',
    },
    '海外聯招會官方網站': {
        'en': 'Overseas Chinese Affairs Council Official Website',
        'id': 'Website Resmi Dewan Urusan Tionghoa Perantauan',
        'ja': '海外聯招会公式サイト',
        'ms': 'Laman Web Rasmi Majlis Hal Ehwal Cina Luar Negara',
        'my': 'နိုင်ငံရပ်ခြား တရုတ်ကျောင်းသားများ ဝင်ခွင့်ကော်မတီ တရားဝင်ဝဘ်ဆိုဒ်',
        'th': 'เว็บไซต์ทางการของสภากิจการชาวจีนโพ้นทะเล',
    },
    '，請選擇你的所在地區查看對應的申請辦法與說明。': {
        'en': '. Please select your region to view the corresponding application procedures and instructions.',
        'id': '. Silakan pilih wilayah Anda untuk melihat prosedur dan instruksi pendaftaran yang sesuai.',
        'ja': '。お住まいの地域を選択して、該当する申請方法と説明をご確認ください。',
        'ms': '. Sila pilih kawasan anda untuk melihat prosedur dan arahan permohonan yang berkaitan.',
        'my': '။ သင်၏တည်နေရာကို ရွေးချယ်ပြီး ကိုက်ညီသောလျှောက်ထားမှုနည်းလမ်းများနှင့် ညွှန်ကြားချက်များကို ကြည့်ပါ။',
        'th': ' กรุณาเลือกภูมิภาคของคุณเพื่อดูขั้นตอนและคำแนะนำในการสมัครที่เกี่ยวข้อง',
    },
    '選擇你的地區': {
        'en': 'Select Your Region',
        'id': 'Pilih Wilayah Anda',
        'ja': '地域を選択してください',
        'ms': 'Pilih Kawasan Anda',
        'my': 'သင်၏ဒေသကို ရွေးချယ်ပါ',
        'th': 'เลือกภูมิภาคของคุณ',
    },
    '香港': {
        'en': 'Hong Kong',
        'id': 'Hong Kong',
        'ja': '香港',
        'ms': 'Hong Kong',
        'my': 'ဟောင်ကောင်',
        'th': 'ฮ่องกง',
    },
    '緬甸': {
        'en': 'Myanmar',
        'id': 'Myanmar',
        'ja': 'ミャンマー',
        'ms': 'Myanmar',
        'my': 'မြန်မာ',
        'th': 'เมียนมา',
    },
    '澳門': {
        'en': 'Macau',
        'id': 'Makau',
        'ja': 'マカオ',
        'ms': 'Macau',
        'my': 'မကာအို',
        'th': 'มาเก๊า',
    },
    '馬來西亞': {
        'en': 'Malaysia',
        'id': 'Malaysia',
        'ja': 'マレーシア',
        'ms': 'Malaysia',
        'my': 'မလေးရှား',
        'th': 'มาเลเซีย',
    },
    '印尼': {
        'en': 'Indonesia',
        'id': 'Indonesia',
        'ja': 'インドネシア',
        'ms': 'Indonesia',
        'my': 'အင်ဒိုနီးရှား',
        'th': 'อินโดนีเซีย',
    },
    '菲律賓': {
        'en': 'Philippines',
        'id': 'Filipina',
        'ja': 'フィリピン',
        'ms': 'Filipina',
        'my': 'ဖိလစ်ပိုင်',
        'th': 'ฟิลิปปินส์',
    },
    '韓國': {
        'en': 'South Korea',
        'id': 'Korea Selatan',
        'ja': '韓国',
        'ms': 'Korea Selatan',
        'my': 'တောင်ကိုရီးယား',
        'th': 'เกาหลีใต้',
    },
    '美國／加拿大': {
        'en': 'USA / Canada',
        'id': 'Amerika / Kanada',
        'ja': 'アメリカ・カナダ',
        'ms': 'Amerika / Kanada',
        'my': 'အမေရိကန် / ကနေဒါ',
        'th': 'สหรัฐฯ / แคนาดา',
    },
    '泰國': {
        'en': 'Thailand',
        'id': 'Thailand',
        'ja': 'タイ',
        'ms': 'Thailand',
        'my': 'ထိုင်းနိုင်ငံ',
        'th': 'ไทย',
    },
    '越南': {
        'en': 'Vietnam',
        'id': 'Vietnam',
        'ja': 'ベトナム',
        'ms': 'Vietnam',
        'my': 'ဗီယက်နမ်',
        'th': 'เวียดนาม',
    },
    '日本': {
        'en': 'Japan',
        'id': 'Jepang',
        'ja': '日本',
        'ms': 'Jepun',
        'my': 'ဂျပန်',
        'th': 'ญี่ปุ่น',
    },
    '新加坡': {
        'en': 'Singapore',
        'id': 'Singapura',
        'ja': 'シンガポール',
        'ms': 'Singapura',
        'my': 'စင်ကာပူ',
        'th': 'สิงคโปร์',
    },
    '其他地區': {
        'en': 'Other Regions',
        'id': 'Wilayah Lainnya',
        'ja': 'その他の地域',
        'ms': 'Kawasan Lain',
        'my': 'အခြားဒေသများ',
        'th': 'ภูมิภาคอื่นๆ',
    },
    '研究所': {
        'en': 'Graduate School',
        'id': 'Program Pascasarjana',
        'ja': '大学院',
        'ms': 'Sekolah Siswazah',
        'my': 'မဟာဘွဲ့ပညာရေး',
        'th': 'บัณฑิตศึกษา',
    },
    '在臺僑生': {
        'en': 'Overseas Chinese in Taiwan',
        'id': 'Diaspora Tionghoa di Taiwan',
        'ja': '台湾在住の僑生',
        'ms': 'Warga Cina Perantauan di Taiwan',
        'my': 'တိုင်ဝမ်တွင်ရှိသော နိုင်ငံရပ်ခြားတရုတ်ကျောင်းသားများ',
        'th': 'นักเรียนจีนโพ้นทะเลในไต้หวัน',
    },
    '海外臺校': {
        'en': 'Overseas Taiwan Schools',
        'id': 'Sekolah Taiwan di Luar Negeri',
        'ja': '海外台湾学校',
        'ms': 'Sekolah Taiwan di Luar Negara',
        'my': 'နိုင်ငံရပ်ခြားရှိ တိုင်ဝမ်ကျောင်းများ',
        'th': 'โรงเรียนไต้หวันในต่างประเทศ',
    },
    '入學申請': {
        'en': 'Admissions',
        'id': 'Pendaftaran Masuk',
        'ja': '入学申請',
        'ms': 'Kemasukan',
        'my': 'ဝင်ခွင့်လျှောက်ထားမှု',
        'th': 'การสมัครเข้าเรียน',
    },
    '依地區查看海外聯招會申請說明，香港、馬來西亞、泰國等': {
        'en': 'View application guides by region: Hong Kong, Malaysia, Thailand, and more',
        'id': 'Lihat panduan pendaftaran per wilayah: Hong Kong, Malaysia, Thailand, dll.',
        'ja': '地域別申請説明（香港・マレーシア・タイなど）を確認できます',
        'ms': 'Lihat panduan permohonan mengikut kawasan: Hong Kong, Malaysia, Thailand, dll.',
        'my': 'ဒေသအလိုက် လျှောက်ထားမှုလမ်းညွှန်ကို ကြည့်ရှုပါ: ဟောင်ကောင်၊ မလေးရှား၊ ထိုင်း စသည်',
        'th': 'ดูคำแนะนำการสมัครตามภูมิภาค: ฮ่องกง มาเลเซีย ไทย และอื่นๆ',
    },
    '入學申請指南': {
        'en': 'Admissions Guide',
        'id': 'Panduan Penerimaan',
        'ja': '入学申請ガイド',
        'ms': 'Panduan Kemasukan',
        'my': 'ဝင်ခွင့်လမ်းညွှန်',
        'th': 'คู่มือการสมัครเข้าเรียน',
    },
    '申請資格、時程、所需文件與注意事項整理': {
        'en': 'Eligibility, timeline, required documents, and important notes',
        'id': 'Kelayakan, jadwal, dokumen yang diperlukan, dan catatan penting',
        'ja': '申請資格・スケジュール・必要書類・注意事項のまとめ',
        'ms': 'Kelayakan, jadual, dokumen yang diperlukan, dan nota penting',
        'my': 'အရည်အချင်းများ၊ အချိန်ဇယား၊ လိုအပ်သောစာရွက်စာတမ်းများနှင့် အရေးကြီးသောမှတ်ချက်များ',
        'th': 'คุณสมบัติ กำหนดการ เอกสารที่ต้องใช้ และข้อควรระวัง',
    },
}

langs = ['en', 'id', 'ja', 'ms', 'my', 'th']
for lang in langs:
    po_path = f'locale/{lang}/LC_MESSAGES/django.po'
    po = polib.pofile(po_path)
    existing = {e.msgid for e in po}
    added = 0
    for msgid, translations in new_strings.items():
        if msgid not in existing:
            entry = polib.POEntry(msgid=msgid, msgstr=translations.get(lang, ''))
            po.append(entry)
            added += 1
        else:
            for e in po:
                if e.msgid == msgid and not e.msgstr:
                    e.msgstr = translations.get(lang, '')
    po.save()
    po.save_as_mofile(po_path.replace('.po', '.mo'))
    print(f'{lang}: added/updated {added} entries')

print('Done.')
