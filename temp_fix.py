import polib
import os

universities = [
    ('國立臺灣大學（NTU）', 'National Taiwan University (NTU)'),
    ('國立政治大學（NCCU）', 'National Chengchi University (NCCU)'),
    ('國立清華大學（NTHU）', 'National Tsing Hua University (NTHU)'),
    ('國立陽明交通大學（NYCU）', 'National Yang Ming Chiao Tung University (NYCU)'),
    ('國立成功大學（NCKU）', 'National Cheng Kung University (NCKU)'),
    ('國立中興大學（NCHU）', 'National Chung Hsing University (NCHU)'),
    ('國立中央大學（NCU）', 'National Central University (NCU)'),
    ('國立中山大學（NSYSU）', 'National Sun Yat-sen University (NSYSU)'),
    ('國立臺灣師範大學（NTNU）', 'National Taiwan Normal University (NTNU)'),
    ('國立臺北大學（NTPU）', 'National Taipei University (NTPU)'),
    ('國立臺南大學（NUTN）', 'National University of Tainan (NUTN)'),
    ('國立嘉義大學（NCYU）', 'National Chiayi University (NCYU)'),
    ('國立東華大學（NDHU）', 'National Dong Hwa University (NDHU)'),
    ('國立暨南國際大學（NCNU）', 'National Chi Nan University (NCNU)'),
    ('國立宜蘭大學（NIU）', 'National Ilan University (NIU)'),
    ('國立臺北教育大學（NTUE）', 'National Taipei University of Education (NTUE)'),
    ('國立臺中教育大學（NTCU）', 'National Taichung University of Education (NTCU)'),
    ('國立屏東大學（NPTU）', 'National Pingtung University (NPTU)'),
    ('國立臺灣體育運動大學（NTUS）', 'National Taiwan University of Sport (NTUS)'),
    ('國立臺北商業大學（NTUB）', 'National Taipei University of Business (NTUB)'),
    ('國立空中大學（NOU）', 'National Open University (NOU)'),
    ('其他（Other）', 'Other')
]

po_file_path = r'c:\studygo\locale\en\LC_MESSAGES\django.po'
mo_file_path = r'c:\studygo\locale\en\LC_MESSAGES\django.mo'

po = polib.pofile(po_file_path)

for zh, en in universities:
    entry = po.find(zh)
    if entry:
        entry.msgstr = en
    else:
        entry = polib.POEntry(
            msgid=zh,
            msgstr=en,
            occurrences=[('users/models.py', '0')]
        )
        po.append(entry)

po.save()
po.save_as_mofile(mo_file_path)
print("Updated English translations!")
