# Generated for chatbot FAQ / knowledge base

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0003_chatattachment'),
    ]

    operations = [
            migrations.CreateModel(
                name='ChatKnowledge',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('category', models.CharField(choices=[('admission', '入學申請'), ('documents', '文件準備'), ('document_verification', '文件驗證'), ('visa', '簽證'), ('financial_proof', '財力證明'), ('language_proof', '語言證明'), ('before_arrival', '來台前準備'), ('entry', '入境規定'), ('country_difference', '國家差異'), ('identity_type', '身分別流程'), ('arrival_transport', '到校交通'), ('orientation', '新生報到'), ('registration_payment', '註冊繳費'), ('student_id', '學生證'), ('arc', '居留證 ARC'), ('health_check', '健檢'), ('insurance', '保險'), ('bank', '銀行開戶'), ('phone', '手機門號'), ('school_system', '校內系統'), ('course', '課務選課'), ('student_status', '學籍'), ('grades', '成績'), ('graduation', '畢業'), ('dorm', '宿舍'), ('renting', '租屋'), ('nhi', '健保'), ('work_permit', '工作證'), ('scholarship', '獎助學金'), ('campus_activity', '校內活動'), ('library', '圖書館'), ('internship', '交換與實習'), ('admin_documents', '行政文件'), ('transportation', '交通'), ('food', '飲食'), ('medical', '醫療'), ('mental_support', '心理支持'), ('emergency', '緊急聯絡'), ('living_cost', '生活費'), ('other', '其他')], default='other', max_length=50, verbose_name='分類')),
                    ('title', models.CharField(max_length=200, verbose_name='繁體中文標題')),
                    ('title_en', models.CharField(blank=True, max_length=200, verbose_name='英文標題')),
                    ('title_vi', models.CharField(blank=True, max_length=200, verbose_name='越文標題')),
                    ('title_my', models.CharField(blank=True, max_length=200, verbose_name='緬文標題')),
                    ('title_id', models.CharField(blank=True, max_length=200, verbose_name='印尼文標題')),
                    ('title_ms', models.CharField(blank=True, max_length=200, verbose_name='馬來文標題')),
                    ('title_th', models.CharField(blank=True, max_length=200, verbose_name='泰文標題')),
                    ('title_ja', models.CharField(blank=True, max_length=200, verbose_name='日文標題')),
                    ('title_ko', models.CharField(blank=True, max_length=200, verbose_name='韓文標題')),
                    ('keywords', models.CharField(blank=True, max_length=500, verbose_name='關鍵字，建議放中文與英文，例如：居留證, ARC, residence permit')),
                    ('content', models.TextField(verbose_name='繁體中文內容')),
                    ('content_en', models.TextField(blank=True, verbose_name='英文內容')),
                    ('content_vi', models.TextField(blank=True, verbose_name='越文內容')),
                    ('content_my', models.TextField(blank=True, verbose_name='緬文內容')),
                    ('content_id', models.TextField(blank=True, verbose_name='印尼文內容')),
                    ('content_ms', models.TextField(blank=True, verbose_name='馬來文內容')),
                    ('content_th', models.TextField(blank=True, verbose_name='泰文內容')),
                    ('content_ja', models.TextField(blank=True, verbose_name='日文內容')),
                    ('content_ko', models.TextField(blank=True, verbose_name='韓文內容')),
                    ('is_active', models.BooleanField(default=True, verbose_name='是否啟用')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='建立時間')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新時間')),
                ],
                options={
                    'verbose_name': 'Chatbot 知識庫 / FAQ',
                    'verbose_name_plural': 'Chatbot 知識庫 / FAQ',
                    'db_table': 'chatbot_knowledge',
                    'ordering': ['category', '-updated_at'],
                },
            ),
        ]
