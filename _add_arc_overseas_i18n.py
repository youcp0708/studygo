# -*- coding: utf-8 -*-
import polib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MSGIDS = [
    "確認護照、入學通知函、在學證明等文件齊全。若需完成健康檢查，請至學校認可醫院辦理（國際事務處可提供名單）。非港澳生及持有效居留證的港澳生可參加校內體檢（約 NT$780）。",
    "前往移民署「外國與外僑學生線上申辦系統」完成帳號註冊，掃描並上傳所需文件：近三個月 2 吋彩色照片、護照、入學通知函及在學證明書。系統操作請參閱官方操作手冊。",
    "不需要。持中華民國籍由僑居地（台灣護照）入台的僑生，具有完整公民身份，無需辦理居留證。本頁服務適用於持外國護照入台就讀的僑生（海外永久居民等）。",
    "可以。可於抵台後參加校內體檢（約 NT$780），或至學校指定醫院完成。注意檢查報告出爐需數天，請盡早安排以避免超過 30 天辦理期限。建議抵台後隔天即至國際事務處詢問體檢安排。",
    "在學期間以「就讀」為居留事由。畢業後如需繼續留台（例如找工作），需在畢業後 30 天內申請變更居留事由為「工作」或「其他」，或在找到合法工作並取得工作許可後辦理變更為「工作」居留事由。建議畢業前盡早規劃，避免居留證失效。",
]

TRANSLATIONS = {
    "en": [
        "Ensure your passport, admission notice, enrollment certificate, and other documents are ready. If a health check is required, visit a school-approved hospital (the Office of International Affairs can provide a list). Non-HK/Macau students and HK/Macau students with a valid resident permit may participate in the on-campus health check (approx. NT$780).",
        "Go to the Immigration Agency's 'Online Application System for Foreign and Overseas Chinese Students', complete account registration, and scan and upload the required documents: a recent 2-inch color photo (taken within the past 3 months), passport, admission notice, and enrollment certificate. Refer to the official user manual for system operation.",
        "No. Overseas Chinese students who hold ROC citizenship and enter Taiwan with a Taiwan passport have full citizen status and do not need to apply for a resident certificate. This page's services apply to overseas Chinese students who enter Taiwan with a foreign passport (overseas permanent residents, etc.).",
        "Yes. You can participate in the on-campus health check (approx. NT$780) after arriving in Taiwan, or have it completed at a school-designated hospital. Note that health check results take several days — please arrange it early to avoid exceeding the 30-day deadline. It is recommended to visit the Office of International Affairs the day after arrival to inquire about health check arrangements.",
        "During the study period, 'study' is the reason for residence. After graduation, if you wish to continue staying in Taiwan (e.g., to look for a job), you must apply to change the reason for residence to 'work' or 'other' within 30 days after graduation, or apply to change it to 'work' after obtaining a legal job and work permit. It is recommended to plan ahead before graduation to avoid the resident certificate becoming invalid.",
    ],
    "vi": [
        "Đảm bảo hộ chiếu, thư thông báo nhập học, chứng nhận nhập học và các tài liệu khác đã đầy đủ. Nếu cần hoàn thành kiểm tra sức khỏe, hãy đến bệnh viện được nhà trường công nhận (Văn phòng Quan hệ Quốc tế có thể cung cấp danh sách). Sinh viên không phải HK/Macau và sinh viên HK/Macau có giấy phép cư trú hợp lệ có thể tham gia kiểm tra sức khỏe trong khuôn viên trường (khoảng NT$780).",
        "Truy cập 'Hệ thống nộp đơn trực tuyến dành cho sinh viên nước ngoài và sinh viên Hoa kiều' của Cơ quan Di trú, hoàn tất đăng ký tài khoản, quét và tải lên các tài liệu cần thiết: ảnh màu 2 inch chụp trong 3 tháng gần đây, hộ chiếu, thư thông báo nhập học và chứng nhận nhập học. Tham khảo hướng dẫn sử dụng chính thức để thao tác hệ thống.",
        "Không cần. Sinh viên Hoa kiều mang quốc tịch Trung Hoa Dân Quốc nhập cảnh Đài Loan bằng hộ chiếu Đài Loan có đầy đủ quyền công dân và không cần xin giấy phép cư trú. Dịch vụ trên trang này dành cho sinh viên Hoa kiều nhập cảnh Đài Loan bằng hộ chiếu nước ngoài (thường trú nhân ở nước ngoài, v.v.).",
        "Có thể. Bạn có thể tham gia kiểm tra sức khỏe trong khuôn viên trường (khoảng NT$780) sau khi đến Đài Loan, hoặc hoàn thành tại bệnh viện được nhà trường chỉ định. Lưu ý kết quả kiểm tra sức khỏe cần vài ngày — vui lòng sắp xếp sớm để tránh vượt quá thời hạn 30 ngày. Khuyến nghị đến Văn phòng Quan hệ Quốc tế vào ngày hôm sau khi đến để hỏi về lịch kiểm tra sức khỏe.",
        "Trong thời gian học tập, 'học tập' là lý do cư trú. Sau khi tốt nghiệp, nếu muốn tiếp tục ở lại Đài Loan (ví dụ: tìm việc làm), bạn phải nộp đơn thay đổi lý do cư trú thành 'công việc' hoặc 'khác' trong vòng 30 ngày sau khi tốt nghiệp, hoặc nộp đơn thay đổi thành 'công việc' sau khi có việc làm hợp pháp và giấy phép lao động. Khuyến nghị lên kế hoạch sớm trước khi tốt nghiệp để tránh giấy phép cư trú bị hết hạn.",
    ],
    "id": [
        "Pastikan paspor, surat pemberitahuan penerimaan, sertifikat pendaftaran, dan dokumen lainnya sudah lengkap. Jika perlu menyelesaikan pemeriksaan kesehatan, kunjungi rumah sakit yang disetujui sekolah (Kantor Urusan Internasional dapat memberikan daftar). Mahasiswa non-HK/Makau dan mahasiswa HK/Makau dengan izin tinggal yang valid dapat mengikuti pemeriksaan kesehatan di kampus (sekitar NT$780).",
        "Kunjungi 'Sistem Pendaftaran Online untuk Pelajar Asing dan Pelajar Tionghoa Perantauan' dari Badan Imigrasi, selesaikan pendaftaran akun, scan dan unggah dokumen yang diperlukan: foto berwarna 2 inci terbaru (diambil dalam 3 bulan terakhir), paspor, surat penerimaan, dan sertifikat pendaftaran. Lihat panduan pengguna resmi untuk pengoperasian sistem.",
        "Tidak perlu. Mahasiswa Tionghoa perantauan yang memegang kewarganegaraan ROC dan memasuki Taiwan dengan paspor Taiwan memiliki status warga negara penuh dan tidak perlu mengajukan sertifikat penduduk. Layanan di halaman ini berlaku untuk mahasiswa Tionghoa perantauan yang memasuki Taiwan dengan paspor asing (penduduk tetap di luar negeri, dll.).",
        "Bisa. Anda dapat mengikuti pemeriksaan kesehatan di kampus (sekitar NT$780) setelah tiba di Taiwan, atau menyelesaikannya di rumah sakit yang ditunjuk sekolah. Perhatikan bahwa hasil pemeriksaan kesehatan membutuhkan beberapa hari — harap atur lebih awal untuk menghindari melebihi batas waktu 30 hari. Disarankan mengunjungi Kantor Urusan Internasional sehari setelah tiba untuk menanyakan jadwal pemeriksaan kesehatan.",
        "Selama masa studi, 'studi' adalah alasan tinggal. Setelah lulus, jika ingin terus tinggal di Taiwan (misalnya, mencari pekerjaan), Anda harus mengajukan perubahan alasan tinggal menjadi 'pekerjaan' atau 'lainnya' dalam 30 hari setelah lulus, atau mengajukan perubahan menjadi 'pekerjaan' setelah mendapatkan pekerjaan legal dan izin kerja. Disarankan untuk merencanakan lebih awal sebelum lulus untuk menghindari sertifikat penduduk menjadi tidak valid.",
    ],
    "ms": [
        "Pastikan pasport, surat tawaran kemasukan, sijil pendaftaran, dan dokumen lain sudah lengkap. Jika perlu menyelesaikan pemeriksaan kesihatan, lawati hospital yang diluluskan sekolah (Pejabat Hal Ehwal Antarabangsa boleh memberikan senarai). Pelajar bukan HK/Macao dan pelajar HK/Macao dengan permit pemastautin yang sah boleh mengambil bahagian dalam pemeriksaan kesihatan di kampus (lebih kurang NT$780).",
        "Pergi ke 'Sistem Permohonan Dalam Talian untuk Pelajar Asing dan Pelajar Cina Perantauan' dari Agensi Imigresen, lengkapkan pendaftaran akaun, imbas dan muat naik dokumen yang diperlukan: foto berwarna 2 inci terbaru (diambil dalam 3 bulan terakhir), pasport, surat tawaran kemasukan, dan sijil pendaftaran. Rujuk panduan pengguna rasmi untuk operasi sistem.",
        "Tidak perlu. Pelajar Cina perantauan yang memegang kewarganegaraan ROC dan memasuki Taiwan dengan pasport Taiwan mempunyai status warganegara penuh dan tidak perlu memohon sijil pemastautin. Perkhidmatan di halaman ini terpakai untuk pelajar Cina perantauan yang memasuki Taiwan dengan pasport asing (pemastautin tetap di luar negara, dll.).",
        "Boleh. Anda boleh mengambil bahagian dalam pemeriksaan kesihatan di kampus (lebih kurang NT$780) selepas tiba di Taiwan, atau menyelesaikannya di hospital yang ditetapkan oleh sekolah. Perhatikan bahawa keputusan pemeriksaan kesihatan memerlukan beberapa hari — sila atur lebih awal untuk mengelakkan melebihi had masa 30 hari. Adalah disyorkan untuk melawati Pejabat Hal Ehwal Antarabangsa sehari selepas tiba untuk bertanya tentang jadual pemeriksaan kesihatan.",
        "Semasa tempoh pengajian, 'pengajian' adalah sebab pemastautin. Selepas tamat pengajian, jika ingin terus tinggal di Taiwan (contohnya, mencari kerja), anda mesti memohon untuk menukar sebab pemastautin kepada 'pekerjaan' atau 'lain-lain' dalam tempoh 30 hari selepas tamat pengajian, atau memohon untuk menukar kepada 'pekerjaan' selepas mendapat pekerjaan yang sah dan permit kerja. Adalah disyorkan untuk merancang lebih awal sebelum tamat pengajian untuk mengelakkan sijil pemastautin menjadi tidak sah.",
    ],
    "th": [
        "ตรวจสอบให้แน่ใจว่าหนังสือเดินทาง จดหมายแจ้งการรับเข้าเรียน ใบรับรองการลงทะเบียน และเอกสารอื่นๆ ครบถ้วน หากต้องการตรวจสุขภาพ ให้ไปที่โรงพยาบาลที่ได้รับการอนุมัติจากโรงเรียน (สำนักงานกิจการนานาชาติสามารถให้รายชื่อได้) นักศึกษาที่ไม่ใช่ HK/มาเก๊า และนักศึกษา HK/มาเก๊าที่มีใบอนุญาตถิ่นที่อยู่ที่ยังมีผลสามารถเข้าร่วมการตรวจสุขภาพในมหาวิทยาลัย (ประมาณ NT$780)",
        "ไปที่ 'ระบบยื่นคำร้องออนไลน์สำหรับนักศึกษาต่างชาติและนักศึกษาชาวจีนโพ้นทะเล' ของสำนักงานตรวจคนเข้าเมือง ดำเนินการลงทะเบียนบัญชี สแกนและอัปโหลดเอกสารที่จำเป็น: รูปถ่ายสีขนาด 2 นิ้วล่าสุด (ถ่ายภายใน 3 เดือนที่ผ่านมา) หนังสือเดินทาง จดหมายรับเข้าเรียน และใบรับรองการลงทะเบียน ดูคู่มือผู้ใช้อย่างเป็นทางการสำหรับการใช้งานระบบ",
        "ไม่จำเป็น นักศึกษาชาวจีนโพ้นทะเลที่ถือสัญชาติ ROC และเดินทางเข้าไต้หวันด้วยหนังสือเดินทางไต้หวันมีสถานะพลเมืองเต็มและไม่จำเป็นต้องสมัครใบรับรองถิ่นที่อยู่ บริการในหน้านี้ใช้กับนักศึกษาชาวจีนโพ้นทะเลที่เดินทางเข้าไต้หวันด้วยหนังสือเดินทางต่างประเทศ (ผู้มีถิ่นที่อยู่ถาวรในต่างประเทศ ฯลฯ)",
        "ได้ คุณสามารถเข้าร่วมการตรวจสุขภาพในมหาวิทยาลัย (ประมาณ NT$780) หลังจากมาถึงไต้หวัน หรือดำเนินการที่โรงพยาบาลที่โรงเรียนกำหนด โปรดทราบว่าผลการตรวจสุขภาพใช้เวลาหลายวัน — โปรดจัดการแต่เนิ่นๆ เพื่อหลีกเลี่ยงการเกินกำหนด 30 วัน แนะนำให้ไปที่สำนักงานกิจการนานาชาติในวันถัดจากที่มาถึงเพื่อสอบถามเกี่ยวกับการจัดการตรวจสุขภาพ",
        "ในช่วงการศึกษา 'การศึกษา' คือเหตุผลสำหรับการพำนัก หลังจากสำเร็จการศึกษา หากต้องการอยู่ต่อในไต้หวัน (เช่น หางาน) คุณต้องสมัครเปลี่ยนเหตุผลการพำนักเป็น 'งาน' หรือ 'อื่นๆ' ภายใน 30 วันหลังจากสำเร็จการศึกษา หรือสมัครเปลี่ยนเป็น 'งาน' หลังจากได้รับงานที่ถูกกฎหมายและใบอนุญาตทำงาน แนะนำให้วางแผนล่วงหน้าก่อนสำเร็จการศึกษาเพื่อหลีกเลี่ยงไม่ให้ใบรับรองถิ่นที่อยู่หมดอายุ",
    ],
    "ko": [
        "여권, 입학 통지서, 재학 증명서 등 서류가 모두 갖춰졌는지 확인하세요. 건강검진을 받아야 하는 경우 학교가 인정한 병원을 방문하세요（국제사무처에서 목록 제공 가능）. 홍콩·마카오 출신이 아닌 학생과 유효한 거류증을 소지한 홍콩·마카오 학생은 교내 건강검진（약 NT$780）에 참여할 수 있습니다.",
        "이민서의 '외국인 및 화교 학생 온라인 신청 시스템'에 접속하여 계정 등록을 완료하고, 필요한 서류를 스캔하여 업로드하세요: 최근 3개월 이내 2인치 컬러 사진, 여권, 입학 통지서, 재학 증명서. 시스템 조작은 공식 사용자 매뉴얼을 참조하세요.",
        "필요 없습니다. 중화민국 국적을 보유하고 대만 여권으로 대만에 입국하는 화교 학생은 완전한 시민권을 가지고 있으므로 거류증을 신청할 필요가 없습니다. 이 페이지의 서비스는 외국 여권으로 대만에 입학하는 화교 학생（해외 영주권자 등）에게 적용됩니다.",
        "가능합니다. 대만 도착 후 교내 건강검진（약 NT$780）에 참여하거나 학교가 지정한 병원에서 완료할 수 있습니다. 검진 결과가 나오는 데 며칠이 걸리므로 30일 기한을 초과하지 않도록 일찍 예약하세요. 도착 다음 날 바로 국제사무처를 방문하여 건강검진 일정을 문의하는 것이 좋습니다.",
        "재학 중에는 '취학'이 거류 사유입니다. 졸업 후 계속 대만에 머물고 싶다면（예: 취업 활동）, 졸업 후 30일 이내에 거류 사유를 '취업' 또는 '기타'로 변경 신청해야 하며, 합법적인 직장을 얻고 취업 허가를 받은 후 '취업' 거류 사유로 변경해야 합니다. 거류증이 만료되지 않도록 졸업 전에 미리 계획하는 것이 좋습니다.",
    ],
    "my": [
        "နိုင်ငံကူး၊ တက်ရောက်ခွင့်ကြေညာချက်၊ တက်ရောက်မှတ်တမ်းနှင့် အခြားစာရွက်စာတမ်းများ ပြည့်စုံမှု စစ်ဆေးပါ။ ကျန်းမာရေးစစ်ဆေးမှု ပြုလုပ်ရန် လိုအပ်ပါက ကျောင်းမှ အသိမှတ်ပြုသောဆေးရုံသို့ သွားပါ (နိုင်ငံတကာရေးရာရုံးမှ စာရင်းပေးနိုင်သည်)။ ဟောင်ကောင်/မကာအိုမဟုတ်သောကျောင်းသားများနှင့် တရားဝင်နေထိုင်ခွင့်ကတ်ရှိသော ဟောင်ကောင်/မကာအိုကျောင်းသားများသည် ကျောင်းတွင်းကျန်းမာရေးစစ်ဆေးမှု (NT$780 ခန့်) တွင် ပါဝင်နိုင်သည်။",
        "လူဝင်မှုကြီးကြပ်ရေးဌာန၏ 'နိုင်ငံခြားသားနှင့် ဟောင်ကောင်ကျောင်းသားများအတွက် အွန်လိုင်းလျှောက်ထားမှုစနစ်' သို့ သွားရောက်ကာ အကောင့်မှတ်ပုံတင်ခြင်းကို ပြီးဆုံးပြီး လိုအပ်သောစာရွက်စာတမ်းများကို စကင်ဖတ်ကာ တင်ပြပါ: လွန်ခဲ့သော ၃ လအတွင်း ရိုက်ကူးထားသော ၂ လက်မ အရောင်ဓာတ်ပုံ၊ နိုင်ငံကူး၊ တက်ရောက်ခွင့်ကြေညာချက်နှင့် တက်ရောက်မှတ်တမ်း။ စနစ်လည်ပတ်မှုအတွက် တရားဝင်အသုံးပြုသူလမ်းညွှန်ကို ကိုးကားပါ။",
        "မလိုအပ်ပါ။ ROC နိုင်ငံသားအဖြစ် ထိုင်ဝမ်နိုင်ငံကူးဖြင့် ထိုင်ဝမ်သို့ ဝင်ရောက်သော ဟောင်ကောင်ကျောင်းသားများသည် ပြည့်ဝသောနိုင်ငံသားအဆင့်ရှိပြီး နေထိုင်ခွင့်လက်မှတ် လျှောက်ထားရန် မလိုအပ်ပါ။ ဤစာမျက်နှာ၏ ဝန်ဆောင်မှုများသည် နိုင်ငံခြားနိုင်ငံကူးဖြင့် ထိုင်ဝမ်သို့ ဝင်ရောက်ကာ ပညာသင်သော ဟောင်ကောင်ကျောင်းသားများ (နိုင်ငံရပ်ခြားတွင် အမြဲနေထိုင်သူများ စသည်) အတွက် သတ်မှတ်သည်။",
        "ရပါသည်။ ထိုင်ဝမ်ရောက်ပြီးနောက် ကျောင်းတွင်းကျန်းမာရေးစစ်ဆေးမှု (NT$780 ခန့်) တွင် ပါဝင်နိုင်သည် သို့မဟုတ် ကျောင်းမှ သတ်မှတ်ထားသောဆေးရုံတွင် ပြီးဆုံးနိုင်သည်။ ကျန်းမာရေးစစ်ဆေးမှုရလဒ်များ ထွက်ရန် ရက်သတ္တပတ်အနည်းငယ်ကြာသောကြောင့် ၃၀ ရက်ကာလကို ကျော်မသွားရန် စောစောစီစဉ်ပါ။ ကျန်းမာရေးစစ်ဆေးမှု စီစဉ်ရန် ရောက်သောနောက်တစ်နေ့ နိုင်ငံတကာရေးရာရုံးသို့ သွားရောက်ရန် အကြံပြုသည်။",
        "ပညာသင်နေစဉ်တွင် 'ပညာသင်' ကို နေထိုင်မှုအကြောင်းပြချက်အဖြစ် သုံးသည်။ ဘွဲ့ရပြီးနောက် ထိုင်ဝမ်တွင် ဆက်လက်နေထိုင်လိုပါက (ဥပမာ: အလုပ်ရှာဖွေရန်)၊ ဘွဲ့ရပြီး ၃၀ ရက်အတွင်း နေထိုင်မှုအကြောင်းပြချက်ကို 'အလုပ်' သို့မဟုတ် 'အခြား' သို့ ပြောင်းလဲရန် လျှောက်ထားရမည်၊ သို့မဟုတ် တရားဝင်အလုပ်ရပြီး အလုပ်ခွင့်မိန့်ရပြီးနောက် 'အလုပ်' နေထိုင်မှုအကြောင်းပြချက်သို့ ပြောင်းလဲရမည်။ နေထိုင်ခွင့်ကတ် သက်တမ်းကုန်မသွားရန် ဘွဲ့မရခင် ကြိုတင်စီစဉ်ရန် အကြံပြုသည်။",
    ],
}

langs = ['en', 'vi', 'id', 'ms', 'th', 'ko', 'my']
for lang in langs:
    path = 'locale/{}/LC_MESSAGES/django.po'.format(lang)
    po = polib.pofile(path)
    em = {e.msgid: e for e in po}
    added = 0
    for i, msgid in enumerate(MSGIDS):
        msgstr = TRANSLATIONS[lang][i]
        if msgid in em:
            if not em[msgid].msgstr.strip():
                em[msgid].msgstr = msgstr
                added += 1
        else:
            entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
            po.append(entry)
            added += 1
    po.save(path)
    po.save_as_mofile(path.replace('.po', '.mo'))
    print('{}: added/updated {} entries, compiled OK'.format(lang, added))
