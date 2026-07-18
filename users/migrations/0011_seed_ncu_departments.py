# 資料遷移：將原本寫死在 profile_setup.html 的 NCU 系所清單灌入資料庫，
# 之後由 Django Admin 管理（新增學校 / 系所不必再改前端）。

from django.db import migrations

NCU_DEPARTMENTS = [
    # (faculty, faculty_en, name, name_en)
    ('文學院', 'College of Liberal Arts', '文學院學士班', 'Bachelor Program, College of Liberal Arts'),
    ('文學院', 'College of Liberal Arts', '中國文學系', 'Department of Chinese Literature'),
    ('文學院', 'College of Liberal Arts', '英美語文學系', 'Department of English'),
    ('文學院', 'College of Liberal Arts', '法國語文學系', 'Department of French'),
    ('理學院', 'College of Science', '理學院學士班', 'Bachelor Program, College of Science'),
    ('理學院', 'College of Science', '物理學系', 'Department of Physics'),
    ('理學院', 'College of Science', '數學系', 'Department of Mathematics'),
    ('理學院', 'College of Science', '化學學系', 'Department of Chemistry'),
    ('理學院', 'College of Science', '光電科學與工程學系', 'Department of Optics and Photonics'),
    ('工學院', 'College of Engineering', '工學院學士班', 'Bachelor Program, College of Engineering'),
    ('工學院', 'College of Engineering', '化學工程與材料工程學系', 'Department of Chemical and Materials Engineering'),
    ('工學院', 'College of Engineering', '土木工程學系', 'Department of Civil Engineering'),
    ('工學院', 'College of Engineering', '機械工程學系', 'Department of Mechanical Engineering'),
    ('管理學院', 'College of Management', '企業管理學系', 'Department of Business Administration'),
    ('管理學院', 'College of Management', '資訊管理學系', 'Department of Information Management'),
    ('管理學院', 'College of Management', '財務金融學系', 'Department of Finance'),
    ('管理學院', 'College of Management', '經濟學系', 'Department of Economics'),
    ('資訊電機學院', 'College of EECS', '資訊電機學院學士班', 'Bachelor Program, College of EECS'),
    ('資訊電機學院', 'College of EECS', '電機工程學系', 'Department of Electrical Engineering'),
    ('資訊電機學院', 'College of EECS', '資訊工程學系', 'Department of Computer Science and Information Engineering'),
    ('資訊電機學院', 'College of EECS', '通訊工程學系', 'Department of Communication Engineering'),
    ('地球科學學院', 'College of Earth Sciences', '地球科學學院學士班', 'Bachelor Program, College of Earth Sciences'),
    ('地球科學學院', 'College of Earth Sciences', '地球科學學系', 'Department of Earth Sciences'),
    ('地球科學學院', 'College of Earth Sciences', '大氣科學學系', 'Department of Atmospheric Sciences'),
    ('地球科學學院', 'College of Earth Sciences', '太空科學與工程學系', 'Department of Space Science and Engineering'),
    ('客家學院', 'College of Hakka Studies', '客家語文暨社會科學學系', 'Department of Hakka Language and Social Sciences'),
    ('生醫理工學院', 'College of Health Sciences and Technology', '生命科學系', 'Department of Life Sciences'),
    ('生醫理工學院', 'College of Health Sciences and Technology', '生醫科學與工程學系', 'Department of Biomedical Sciences and Engineering'),
]


def seed_departments(apps, schema_editor):
    Department = apps.get_model('users', 'Department')
    if Department.objects.filter(university='NCU').exists():
        return  # 已有資料就不重複灌
    Department.objects.bulk_create([
        Department(
            university='NCU',
            faculty=faculty,
            faculty_en=faculty_en,
            name=name,
            name_en=name_en,
            order=i,
        )
        for i, (faculty, faculty_en, name, name_en) in enumerate(NCU_DEPARTMENTS)
    ])


def remove_departments(apps, schema_editor):
    Department = apps.get_model('users', 'Department')
    Department.objects.filter(university='NCU').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_department'),
    ]

    operations = [
        migrations.RunPython(seed_departments, remove_departments),
    ]
