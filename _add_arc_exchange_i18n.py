# -*- coding: utf-8 -*-
import polib, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MSGIDS = [
    "香港、澳門學生依據《香港澳門關係條例》來台就學，入台方式及居留申請程序與一般外籍生不同。本頁整理港澳生常見的入台文件、居留證申請流程及注意事項。",
    "港澳生持居留證可申請工讀許可（每週不超過 20 小時）。需向學校取得工讀同意書後，至勞動部辦理工作許可。在校內工讀（如圖書館、系辦助理）通常只需學校同意，手續較簡便。未取得合法工作許可的工作行為依法屬違規，請務必事先申請。",
    "即可申請延期。延期所需文件與初次申請類似（在學證明書、居留證正本、照片等），無需再繳健康檢查費。延期規費 NT$500。建議提早辦理以避免逾期。",
    "可以。取得居留證後，透過學校衛生保健組辦理加保即可。保費依年度費率由學校代扣，學生費率比一般標準低。加保後就醫診所門診費用約 NT$150，享有與台灣學生相同的健保保障。",
    "大多數學校會在開學初舉辦團體辦理場次，OIA 統一帶隊至移民署。建議迎新報到後立即前往 OIA 確認是否有統一辦理安排，以便提早準備所需文件，節省自行前往的時間。",
]

TRANSLATIONS = {
    "en": [
        "Hong Kong and Macau students studying in Taiwan under the Hong Kong and Macau Relations Act enter Taiwan and apply for residence permits through a different process than regular international students. This page summarizes common entry documents, residence permit application procedures, and important notes for HK/Macau students.",
        "HK/Macau students with a resident permit may apply for a work-study permit (not exceeding 20 hours per week). A school consent form must be obtained before applying for a work permit at the Ministry of Labor. On-campus work (such as library or department office assistants) typically only requires school approval and involves simpler procedures. Working without a legal work permit is a violation of the law — please apply in advance.",
        "may apply for an extension. Documents required for extension are similar to the initial application (enrollment certificate, original resident permit, photos, etc.), and no additional health check fee is required. The extension fee is NT$500. It is recommended to apply early to avoid expiry.",
        "Yes. After obtaining a resident permit, NHI enrollment can be done through the school's Health Center. Premiums are deducted by the school based on the annual rate; the student rate is lower than the standard rate. After enrollment, clinic consultation fees are approximately NT$150, with the same NHI coverage as Taiwanese students.",
        "Most schools hold group application sessions at the beginning of the semester, with OIA leading students to the Immigration Agency together. It is recommended to visit OIA immediately after orientation registration to confirm whether a group session is available, so you can prepare the required documents early and save time by not going on your own.",
    ],
    "vi": [
        "Sinh viên Hồng Kông và Ma Cao đến Đài Loan học tập theo Đạo luật Quan hệ Hồng Kông và Ma Cao có phương thức nhập cảnh và thủ tục xin giấy phép cư trú khác với sinh viên quốc tế thông thường. Trang này tóm tắt các tài liệu nhập cảnh phổ biến, quy trình xin giấy phép cư trú và lưu ý quan trọng dành cho sinh viên HK/Macau.",
        "Sinh viên HK/Macau có giấy phép cư trú có thể xin giấy phép làm thêm (không quá 20 giờ mỗi tuần). Cần lấy giấy chấp thuận làm thêm từ nhà trường trước khi xin giấy phép làm việc tại Bộ Lao động. Làm thêm trong khuôn viên trường (như thư viện, trợ lý văn phòng khoa) thường chỉ cần sự chấp thuận của nhà trường với thủ tục đơn giản hơn. Làm việc mà không có giấy phép hợp pháp là vi phạm pháp luật — vui lòng nộp đơn trước.",
        "có thể xin gia hạn. Tài liệu cần thiết để gia hạn tương tự đơn xin lần đầu (chứng nhận nhập học, giấy phép cư trú gốc, ảnh, v.v.) và không cần trả thêm phí kiểm tra sức khỏe. Phí gia hạn là NT$500. Khuyến nghị nộp đơn sớm để tránh hết hạn.",
        "Có thể. Sau khi có giấy phép cư trú, có thể đăng ký NHI qua trung tâm y tế của trường. Phí bảo hiểm được khấu trừ bởi nhà trường theo tỷ lệ hàng năm; tỷ lệ học sinh thấp hơn mức tiêu chuẩn. Sau khi đăng ký, phí khám ngoại trú khoảng NT$150, được bảo hiểm NHI giống như sinh viên Đài Loan.",
        "Hầu hết các trường tổ chức buổi nộp đơn tập thể vào đầu học kỳ, với OIA dẫn sinh viên đến Cơ quan Di trú cùng nhau. Khuyến nghị đến OIA ngay sau khi đăng ký định hướng để xác nhận có buổi tập thể không, giúp bạn chuẩn bị tài liệu sớm và tiết kiệm thời gian tự đi.",
    ],
    "id": [
        "Mahasiswa Hong Kong dan Makau yang belajar di Taiwan berdasarkan Undang-Undang Hubungan Hong Kong dan Makau memiliki cara masuk Taiwan dan prosedur permohonan izin tinggal yang berbeda dari mahasiswa internasional biasa. Halaman ini merangkum dokumen masuk yang umum, prosedur permohonan izin tinggal, dan catatan penting untuk mahasiswa HK/Makau.",
        "Mahasiswa HK/Makau dengan izin tinggal dapat mengajukan izin kerja paruh waktu (tidak lebih dari 20 jam per minggu). Surat persetujuan kerja paruh waktu harus diperoleh dari sekolah sebelum mengajukan izin kerja di Kementerian Tenaga Kerja. Kerja paruh waktu di kampus (seperti perpustakaan, asisten kantor jurusan) biasanya hanya memerlukan persetujuan sekolah dengan prosedur yang lebih sederhana. Bekerja tanpa izin kerja yang sah melanggar hukum — harap ajukan terlebih dahulu.",
        "dapat mengajukan perpanjangan. Dokumen yang diperlukan untuk perpanjangan serupa dengan permohonan awal (sertifikat pendaftaran, izin tinggal asli, foto, dll.) dan tidak perlu membayar biaya pemeriksaan kesehatan tambahan. Biaya perpanjangan adalah NT$500. Disarankan untuk mengajukan lebih awal untuk menghindari kedaluwarsa.",
        "Bisa. Setelah mendapatkan izin tinggal, pendaftaran NHI dapat dilakukan melalui pusat kesehatan sekolah. Premi dipotong oleh sekolah berdasarkan tarif tahunan; tarif pelajar lebih rendah dari tarif standar. Setelah terdaftar, biaya konsultasi klinik rawat jalan sekitar NT$150, dengan perlindungan NHI yang sama seperti mahasiswa Taiwan.",
        "Kebanyakan sekolah mengadakan sesi permohonan kelompok di awal semester, dengan OIA memimpin mahasiswa ke Badan Imigrasi bersama-sama. Disarankan untuk mengunjungi OIA segera setelah pendaftaran orientasi untuk memastikan apakah ada sesi kelompok, sehingga Anda dapat mempersiapkan dokumen yang diperlukan lebih awal dan menghemat waktu dengan tidak pergi sendiri.",
    ],
    "ms": [
        "Pelajar Hong Kong dan Macao yang belajar di Taiwan di bawah Akta Hubungan Hong Kong dan Macao mempunyai cara masuk Taiwan dan prosedur permohonan permit pemastautin yang berbeza daripada pelajar antarabangsa biasa. Halaman ini meringkaskan dokumen kemasukan yang biasa, prosedur permohonan permit pemastautin dan nota penting untuk pelajar HK/Macao.",
        "Pelajar HK/Macao dengan permit pemastautin boleh memohon permit kerja sambil belajar (tidak melebihi 20 jam seminggu). Surat kebenaran kerja sambil belajar mesti diperolehi daripada sekolah sebelum memohon permit kerja di Kementerian Buruh. Kerja sambil belajar di kampus (seperti perpustakaan, pembantu pejabat jabatan) biasanya hanya memerlukan kelulusan sekolah dengan prosedur yang lebih mudah. Bekerja tanpa permit kerja yang sah adalah pelanggaran undang-undang — sila mohon terlebih dahulu.",
        "boleh memohon perpanjangan. Dokumen yang diperlukan untuk perpanjangan adalah serupa dengan permohonan awal (sijil pendaftaran, permit pemastautin asal, foto, dll.) dan tidak perlu membayar bayaran pemeriksaan kesihatan tambahan. Bayaran perpanjangan ialah NT$500. Adalah disyorkan untuk memohon lebih awal bagi mengelakkan tamat tempoh.",
        "Boleh. Selepas mendapat permit pemastautin, pendaftaran NHI boleh dilakukan melalui pusat kesihatan sekolah. Premium ditolak oleh sekolah berdasarkan kadar tahunan; kadar pelajar lebih rendah daripada kadar standard. Selepas pendaftaran, bayaran perundingan klinik pesakit luar kira-kira NT$150, dengan perlindungan NHI yang sama seperti pelajar Taiwan.",
        "Kebanyakan sekolah mengadakan sesi permohonan berkumpulan pada permulaan semester, dengan OIA memimpin pelajar ke Agensi Imigresen bersama-sama. Adalah disyorkan untuk melawati OIA dengan segera selepas pendaftaran orientasi untuk mengesahkan sama ada ada sesi berkumpulan, supaya anda boleh menyediakan dokumen yang diperlukan lebih awal dan menjimatkan masa dengan tidak pergi sendiri.",
    ],
    "th": [
        "นักศึกษาฮ่องกงและมาเก๊าที่มาเรียนในไต้หวันตามพระราชบัญญัติความสัมพันธ์ฮ่องกงและมาเก๊า มีวิธีการเดินทางเข้าไต้หวันและขั้นตอนการขอใบอนุญาตถิ่นที่อยู่ที่แตกต่างจากนักศึกษาต่างชาติทั่วไป หน้านี้สรุปเอกสารการเข้าประเทศที่พบบ่อย ขั้นตอนการขอใบอนุญาตถิ่นที่อยู่ และข้อควรระวังสำหรับนักศึกษา HK/มาเก๊า",
        "นักศึกษา HK/มาเก๊าที่มีใบอนุญาตถิ่นที่อยู่สามารถขอใบอนุญาตทำงานพาร์ทไทม์ (ไม่เกิน 20 ชั่วโมงต่อสัปดาห์) ต้องขอหนังสือยินยอมจากโรงเรียนก่อนยื่นขอใบอนุญาตทำงานที่กระทรวงแรงงาน การทำงานในมหาวิทยาลัย (เช่น ห้องสมุด ผู้ช่วยสำนักงานภาควิชา) โดยปกติต้องได้รับการอนุมัติจากโรงเรียนเท่านั้นและมีขั้นตอนที่ง่ายกว่า การทำงานโดยไม่มีใบอนุญาตทำงานที่ถูกกฎหมายถือเป็นการละเมิดกฎหมาย — กรุณายื่นคำร้องล่วงหน้า",
        "สามารถยื่นขอต่ออายุได้ เอกสารที่จำเป็นสำหรับการต่ออายุคล้ายกับการยื่นครั้งแรก (ใบรับรองการลงทะเบียน ใบอนุญาตถิ่นที่อยู่ต้นฉบับ ภาพถ่าย ฯลฯ) และไม่ต้องจ่ายค่าตรวจสุขภาพเพิ่มเติม ค่าธรรมเนียมต่ออายุคือ NT$500 แนะนำให้ยื่นคำร้องแต่เนิ่นๆ เพื่อหลีกเลี่ยงการหมดอายุ",
        "ได้ หลังจากได้รับใบอนุญาตถิ่นที่อยู่ สามารถลงทะเบียน NHI ผ่านศูนย์สุขภาพของโรงเรียน เบี้ยประกันหักโดยโรงเรียนตามอัตราประจำปี อัตรานักศึกษาต่ำกว่าอัตรามาตรฐาน หลังจากลงทะเบียน ค่าปรึกษาคลินิกผู้ป่วยนอกประมาณ NT$150 ได้รับความคุ้มครอง NHI เหมือนกับนักศึกษาไต้หวัน",
        "โรงเรียนส่วนใหญ่จัดเซสชันการยื่นคำร้องแบบกลุ่มในช่วงต้นภาคเรียน โดย OIA นำนักศึกษาไปที่สำนักงานตรวจคนเข้าเมืองด้วยกัน แนะนำให้ไปที่ OIA ทันทีหลังจากลงทะเบียนรับน้องเพื่อยืนยันว่ามีเซสชันแบบกลุ่มหรือไม่ เพื่อให้คุณสามารถเตรียมเอกสารที่จำเป็นล่วงหน้าและประหยัดเวลาโดยไม่ต้องไปเอง",
    ],
    "ko": [
        "홍콩·마카오 학생은 《홍콩마카오관계조례》에 따라 대만에서 유학하며, 대만 입국 방식 및 거류 신청 절차가 일반 외국인 학생과 다릅니다. 이 페이지에서는 홍콩·마카오 학생의 입국 서류, 거류증 신청 절차 및 주의 사항을 정리합니다.",
        "홍콩·마카오 학생은 거류증을 소지하면 아르바이트 허가를 신청할 수 있습니다（주당 20시간 이하）. 학교에서 아르바이트 동의서를 받은 후 노동부에서 취업 허가를 받아야 합니다. 교내 아르바이트（도서관, 학과 조교 등）는 일반적으로 학교 동의만 필요하며 절차가 더 간단합니다. 합법적인 취업 허가 없이 일하는 것은 법률 위반입니다 — 반드시 사전에 신청하세요.",
        "연장을 신청할 수 있습니다. 연장에 필요한 서류는 최초 신청과 유사하며（재학 증명서, 거류증 원본, 사진 등）, 건강검진 비용은 다시 납부하지 않아도 됩니다. 연장 수수료는 NT$500입니다. 기한이 지나지 않도록 일찍 신청하는 것이 좋습니다.",
        "가능합니다. 거류증을 받은 후 학교 보건소를 통해 건강보험에 가입할 수 있습니다. 보험료는 학교에서 연간 요율에 따라 대신 공제하며, 학생 요율은 일반 기준보다 낮습니다. 가입 후 의원 외래 진료비는 약 NT$150이며, 대만 학생과 동일한 건강보험 혜택을 받을 수 있습니다.",
        "대부분의 학교는 학기 초에 단체 신청 행사를 개최하며, OIA가 학생들을 이민서로 단체 인솔합니다. 오리엔테이션 등록 직후 OIA를 방문하여 단체 신청 일정이 있는지 확인하고, 필요한 서류를 미리 준비하여 직접 가는 시간을 절약하는 것이 좋습니다.",
    ],
    "my": [
        "ဟောင်ကောင်နှင့် မကာအို ကျောင်းသားများသည် ဟောင်ကောင်မကာအိုဆက်ဆံရေးဥပဒေအရ ထိုင်ဝမ်တွင် ပညာသင်ကြားရာ၊ ထိုင်ဝမ်ဝင်ရောက်နည်းနှင့် နေထိုင်ခွင့်လျှောက်ထားမှုဆိုင်ရာ လုပ်ငန်းစဉ်သည် ပုံမှန်နိုင်ငံတကာကျောင်းသားများနှင့် မတူပါ။ ဤစာမျက်နှာတွင် HK/မကာအို ကျောင်းသားများအတွက် ဝင်ရောက်ရေးစာရွက်စာတမ်းများ၊ နေထိုင်ခွင့်လျှောက်ထားမှု လုပ်ငန်းစဉ်နှင့် မှတ်ချက်အရေးကြီးသောအချက်များကို အကျဉ်းချုပ်ဖော်ပြသည်။",
        "HK/မကာအို ကျောင်းသားများသည် နေထိုင်ခွင့်ကတ်ဖြင့် အချိန်ပိုင်းအလုပ်ခွင့်မိန့် (တစ်ပတ်တွင် ၂၀ နာရီမကျော်) လျှောက်ထားနိုင်သည်။ လုပ်ငန်းဝန်ကြီးဌာနတွင် အလုပ်ခွင့်မိန့်လျှောက်ထားမတိုင်မီ ကျောင်းမှ သဘောတူညီချက်ရယူရမည်။ ကျောင်းတွင်းအချိန်ပိုင်းအလုပ် (ဥပမာ: စာကြည့်တိုက်၊ ဌာနရုံးကူညီသူ) တွင် ကျောင်း၏ သဘောတူညီချက်သာ လိုအပ်ပြီး လုပ်ငန်းစဉ်ပိုမိုလွယ်ကူသည်။ တရားဝင်အလုပ်ခွင့်မိန့်မရဘဲ လုပ်ကိုင်ခြင်းသည် ဥပဒေချိုးဖောက်မှုဖြစ်သည် — ကြိုတင်လျှောက်ထားပါ။",
        "တိုးမြှင့်ရန် လျှောက်ထားနိုင်သည်။ တိုးမြှင့်ရန် လိုအပ်သောစာရွက်စာတမ်းများသည် ပထမဆုံးလျှောက်ထားမှုနှင့် ဆင်တူပြီး (တက်ရောက်မှတ်တမ်း၊ နေထိုင်ခွင့်ကတ်မူရင်း၊ ဓာတ်ပုံ စသည်)၊ ကျန်းမာရေးစစ်ဆေးမှုအတွက် ထပ်မံပေးဆပ်ရန် မလိုအပ်ပါ။ တိုးမြှင့်ကြေ NT$500 ဖြစ်သည်။ သက်တမ်းကုန်မသွားရန် စောစောလျှောက်ထားရန် အကြံပြုသည်။",
        "ရပါသည်။ နေထိုင်ခွင့်ကတ်ရပြီးနောက် ကျောင်း၏ ကျန်းမာရေးစင်တာမှတဆင့် NHI တွင် မှတ်ပုံတင်နိုင်သည်။ အာမခံပရီမီယံကို ကျောင်းက နှစ်ချင်းနှုန်းတွက်ကာ ကောက်ယူသည်; ကျောင်းသားနှုန်းသည် မူလနှုန်းထားထက် နည်းသည်။ မှတ်ပုံတင်ပြီးနောက် ဆေးခန်းကုသမှုကြေ NT$150 ခန့်ဖြစ်ပြီး ထိုင်ဝမ်ကျောင်းသားများနှင့် တူညီသော NHI အကာအကွယ်ရသည်။",
        "ကျောင်းအများစုသည် ဘာသာနှစ်ပထမတွင် အုပ်စုနဲ့ လျှောက်ထားသောပွဲများ ကျင်းပပြီး OIA က ကျောင်းသားများကို လူဝင်မှုကြီးကြပ်ရေးဌာနသို့ အတူဦးဆောင်ခေါ်သွားသည်။ အုပ်စုနဲ့ လျှောက်ထားသောပွဲ ရှိမရှိ အတည်ပြုရန် မိတ်ဆက်ပွဲ မှတ်ပုံတင်ပြီးချင်းပင် OIA သို့ သွားရောက်ရန် အကြံပြုသည်; လိုအပ်သောစာရွက်စာတမ်းများကို ကြိုတင်ပြင်ဆင်ကာ မိမိကိုယ်တိုင်သွားရသောအချိန်ကို သက်သာစေသည်။",
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
