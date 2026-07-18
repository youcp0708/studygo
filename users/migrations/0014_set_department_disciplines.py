# 資料遷移：為已灌入的 NCU 系所標上 18 學群分類，
# AI 小老師依此識別學生的學科背景。

from django.db import migrations

DEPT_DISCIPLINE = {
    '文學院學士班': 'humanities',
    '中國文學系': 'humanities',
    '英美語文學系': 'foreign_lang',
    '法國語文學系': 'foreign_lang',
    '理學院學士班': 'math_science',
    '物理學系': 'math_science',
    '數學系': 'math_science',
    '化學學系': 'math_science',
    '光電科學與工程學系': 'engineering',
    '工學院學士班': 'engineering',
    '化學工程與材料工程學系': 'engineering',
    '土木工程學系': 'engineering',
    '機械工程學系': 'engineering',
    '企業管理學系': 'management',
    '資訊管理學系': 'management',
    '財務金融學系': 'finance',
    '經濟學系': 'finance',
    '資訊電機學院學士班': 'info',
    '電機工程學系': 'engineering',
    '資訊工程學系': 'info',
    '通訊工程學系': 'engineering',
    '地球科學學院學士班': 'earth_env',
    '地球科學學系': 'earth_env',
    '大氣科學學系': 'earth_env',
    '太空科學與工程學系': 'earth_env',
    '客家語文暨社會科學學系': 'social_psy',
    '生命科學系': 'life_science',
    '生醫科學與工程學系': 'medical',
}


def set_disciplines(apps, schema_editor):
    Department = apps.get_model('users', 'Department')
    for name, discipline in DEPT_DISCIPLINE.items():
        Department.objects.filter(name=name).update(discipline=discipline)


def unset_disciplines(apps, schema_editor):
    Department = apps.get_model('users', 'Department')
    Department.objects.filter(name__in=DEPT_DISCIPLINE.keys()).update(discipline='')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_department_discipline'),
    ]

    operations = [
        migrations.RunPython(set_disciplines, unset_disciplines),
    ]
