from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from chatbot.models import ChatKnowledge, ChatSession, ChatMessage, ChatFeedback
from chatbot.services import (
    build_local_personal_answer,
    build_school_context,
    build_tutor_context,
    contains_crisis_keywords,
    detect_friend_domain_query,
    detect_helper_domain_hit,
    detect_question_language,
    detect_weather_query,
    fetch_typhoon_bulletin,
    fetch_weather_forecast,
    generate_ai_reply,
    get_role_instructions,
    get_student_county,
    get_student_discipline,
    search_knowledge_items,
)
from users.models import CustomUser, School, SchoolUnit, StudentProfile


class DetectQuestionLanguageTest(TestCase):
    def test_indonesian_unique_marker(self):
        self.assertEqual(detect_question_language('kapan saya bisa mendaftar kuliah?'), 'id')

    def test_malay_unique_marker(self):
        self.assertEqual(detect_question_language('bila saya boleh daftar universiti?'), 'ms')

    def test_english(self):
        self.assertEqual(detect_question_language('What is ARC?'), 'en')


@override_settings(OPENAI_API_KEY='test-key')
class KnowledgeDirectShortcutTest(TestCase):
    """知識庫直接命中（不呼叫 OpenAI）時，整段回覆必須跟著提問語言走"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='chat@test.com', password='pw', name='Chat Tester'
        )
        ChatKnowledge.objects.create(
            category='arc',
            title='ARC 居留證',
            title_en='ARC (Alien Resident Certificate)',
            keywords='ARC, 居留證, residence permit',
            content='入境後 30 天內須辦理居留證。',
            content_en='You must apply for an ARC within 30 days of arrival.',
            bot_type='helper',
            source_url='https://www.immigration.gov.tw/',
        )

    def _reply(self, question):
        result = generate_ai_reply(
            user=self.user,
            question=question,
            recent_messages=[],
            ai_mode='helper',
        )
        self.assertEqual(result['source'], 'knowledge_base_direct')
        return result['reply']

    def test_english_question_gets_english_shortcut_reply(self):
        reply = self._reply('What is ARC?')
        self.assertIn('You must apply for an ARC within 30 days of arrival.', reply)
        self.assertNotIn('入境後 30 天內須辦理居留證。', reply)

    def test_chinese_question_gets_chinese_shortcut_reply(self):
        reply = self._reply('居留證是什麼？')
        self.assertIn('入境後 30 天內須辦理居留證。', reply)

    def test_reply_contains_official_source_link(self):
        reply = self._reply('居留證是什麼？')
        self.assertIn('https://www.immigration.gov.tw/', reply)


class RoleInstructionsTest(TestCase):
    """角色人格指令：所有前端可選的組合都必須有對應指令，不可靜默失效"""

    def test_default_friend_personality_exists(self):
        self.assertTrue(get_role_instructions('朋友', '好朋友').strip())

    def test_all_frontend_personalities_have_instructions(self):
        combos = [
            ('小老師', '課業輔助'), ('小老師', '生活指導'),
            ('朋友', '好朋友'), ('朋友', '瘋玩'), ('朋友', '安靜陪伴'),
            ('朋友', '沉穩可靠'), ('朋友', '火爆脾氣'),
        ]
        for role, personality in combos:
            self.assertTrue(
                get_role_instructions(role, personality).strip(),
                f'({role}, {personality}) 沒有對應的角色指令'
            )

    def test_unknown_personality_falls_back_to_role_default(self):
        # 使用者自訂人格名稱時，退回該角色預設而不是無人格
        self.assertTrue(get_role_instructions('朋友', '自訂的名字').strip())

    def test_no_role_returns_empty(self):
        self.assertEqual(get_role_instructions('', ''), '')


class CrisisKeywordTest(TestCase):
    """多語危機偵測：9 語關鍵字保底"""

    def test_detects_multilingual_crisis(self):
        samples = [
            '我最近一直想死',
            'i want to die',
            'em muốn chết quá',
            'aku ingin mati',
            'ฉันอยากตาย',
            'もう死にたい',
            '죽고 싶어요',
        ]
        for text in samples:
            self.assertTrue(contains_crisis_keywords(text), f'未偵測到危機訊息: {text}')

    def test_normal_message_not_flagged(self):
        self.assertFalse(contains_crisis_keywords('今天天氣不錯，想去吃火鍋'))


def make_profile(user, **overrides):
    data = dict(
        nationality='Vietnam',
        university='NCU',
        identity_type='foreign_student',
        admission_status='pre_arrival',
        expected_arrival=timezone.localdate() + timedelta(days=1),
    )
    data.update(overrides)
    return StudentProfile.objects.create(user=user, **data)


class LocalPersonalAnswerTest(TestCase):
    """本地個人化引擎：以真實任務資料組出個人化回答（零幻覺）"""

    def setUp(self):
        from flows.models import FlowStage, Task, StudentTask
        self.user = CustomUser.objects.create_user(
            email='personal@test.com', password='pw', name='Personal'
        )
        self.profile = make_profile(self.user)
        stage = FlowStage.objects.create(name='抵台後', order=2)
        self.task = Task.objects.create(
            stage=stage,
            title='辦理 ARC 居留證',
            deadline_type='from_arrival',
            deadline_days=30,
            order=1,
        )
        StudentTask.objects.create(student=self.profile, task=self.task, status='in_progress')

    def test_answer_contains_real_task_status_and_deadline(self):
        answer = build_local_personal_answer(self.user, '居留證要怎麼辦？', 'zh-hant')
        self.assertIsNotNone(answer)
        self.assertIn('辦理 ARC 居留證', answer)
        self.assertIn('進行中', answer)
        due = (self.profile.expected_arrival + timedelta(days=30)).strftime('%Y-%m-%d')
        self.assertIn(due, answer)

    def test_answer_localized_to_english(self):
        answer = build_local_personal_answer(self.user, 'How do I apply for ARC?', 'en')
        self.assertIsNotNone(answer)
        self.assertIn('In progress', answer)

    def test_no_profile_returns_none(self):
        other = CustomUser.objects.create_user(email='nop@test.com', password='pw', name='NoP')
        self.assertIsNone(build_local_personal_answer(other, '居留證？', 'zh-hant'))


@override_settings(OPENAI_API_KEY='test-key')
class FollowupSuggestionsTest(TestCase):
    """追問建議：由知識庫同分類條目的多語標題生成"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='sug@test.com', password='pw', name='Sug'
        )
        ChatKnowledge.objects.create(
            category='arc', title='ARC 居留證申請',
            keywords='ARC, 居留證', content='入境後 30 天內辦理。', bot_type='helper',
        )
        # 同分類、但這次提問不會命中的條目 → 應成為「你可能還想問」建議
        ChatKnowledge.objects.create(
            category='arc', title='外僑延期停留規定',
            title_en='Extension of Stay',
            keywords='延期', content='到期前 30 天可申請延期。', bot_type='helper',
        )

    def test_shortcut_reply_includes_suggestions(self):
        result = generate_ai_reply(
            user=self.user, question='居留證是什麼？',
            recent_messages=[], ai_mode='helper',
        )
        self.assertEqual(result['source'], 'knowledge_base_direct')
        self.assertIn('外僑延期停留規定', result.get('suggestions', []))


@override_settings(OPENAI_API_KEY='')
class CrisisSafetyNetAPITest(TestCase):
    """危機保底：friend 模式命中危機關鍵字時，回覆一定附上可撥打的求助電話"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='crisis@test.com', password='pw', name='Crisis'
        )
        make_profile(self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_crisis_message_gets_tel_links(self):
        response = self.client.post('/chatbot/api/message/', {
            'message': '我最近想死，撐不下去了',
            'ai_mode': 'friend',
        })
        self.assertEqual(response.status_code, 200)
        parts = [m['content'] for m in response.data['data']['assistant_messages']]
        self.assertTrue(any('tel:' in p for p in parts), '危機訊息的回覆未附上求助電話')

    def test_normal_message_no_forced_resources(self):
        response = self.client.post('/chatbot/api/message/', {
            'message': '今天想去散步',
            'ai_mode': 'friend',
        })
        parts = [m['content'] for m in response.data['data']['assistant_messages']]
        self.assertFalse(any('119' in p for p in parts))


class FeedbackAPITest(TestCase):
    """回饋閉環：學生對 AI 回覆按讚 / 倒讚"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='fb@test.com', password='pw', name='FB'
        )
        self.other = CustomUser.objects.create_user(
            email='other@test.com', password='pw', name='Other'
        )
        session = ChatSession.objects.create(user=self.user, title='t', ai_mode='helper')
        self.msg = ChatMessage.objects.create(session=session, role='assistant', content='答覆')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_feedback_saved_and_updatable(self):
        res = self.client.post('/chatbot/api/feedback/', {'message_id': self.msg.id, 'rating': 'down'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(ChatFeedback.objects.get(message=self.msg).rating, 'down')

        # 改變心意 → 覆蓋而不是新增
        self.client.post('/chatbot/api/feedback/', {'message_id': self.msg.id, 'rating': 'up'})
        self.assertEqual(ChatFeedback.objects.count(), 1)
        self.assertEqual(ChatFeedback.objects.get(message=self.msg).rating, 'up')

    def test_cannot_rate_others_message(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.post('/chatbot/api/feedback/', {'message_id': self.msg.id, 'rating': 'up'})
        self.assertEqual(res.status_code, 404)

    def test_invalid_rating_rejected(self):
        res = self.client.post('/chatbot/api/feedback/', {'message_id': self.msg.id, 'rating': 'meh'})
        self.assertEqual(res.status_code, 400)


class DisciplineKnowledgeSeedTest(TestCase):
    """18 學群知識包：資料遷移應灌入 18 則學群知識 + 3 則通用知識"""

    def test_all_disciplines_seeded(self):
        from users.models import DISCIPLINE_CHOICES
        for code, label in DISCIPLINE_CHOICES:
            self.assertTrue(
                ChatKnowledge.objects.filter(discipline=code, is_active=True).exists(),
                f'{label}（{code}）沒有對應的課業知識'
            )

    def test_general_course_knowledge_seeded(self):
        count = ChatKnowledge.objects.filter(discipline='', category='course').count()
        self.assertGreaterEqual(count, 3)


class StudentDisciplineTest(TestCase):
    """系所 → 學群識別：Department 查表優先，關鍵字分類為備援"""

    def _user(self, department):
        user = CustomUser.objects.create_user(
            email=f'{department[:4]}@test.com', password='pw', name='D'
        )
        make_profile(user)
        profile = user.student_profile
        profile.department = department
        profile.save()
        return user

    def test_department_table_lookup(self):
        # 資訊工程學系已在 Department 資料表中標為資訊學群
        user = self._user('資訊工程學系')
        code, label = get_student_discipline(user)
        self.assertEqual(code, 'info')
        self.assertEqual(label, '資訊學群')

    def test_keyword_fallback_for_unknown_department(self):
        # 「護理系」不在 Department 資料表（NCU 沒有），走關鍵字分類
        user = self._user('護理系')
        code, _label = get_student_discipline(user)
        self.assertEqual(code, 'medical')

    def test_keyword_order_specific_first(self):
        # 「化學工程」要被分到工程學群，而不是數理化學群
        user = self._user('化學工程學系')
        code, _label = get_student_discipline(user)
        self.assertEqual(code, 'engineering')

    def test_management_info_disambiguation(self):
        # 「資訊管理」屬管理學群，不是資訊學群
        user = self._user('資訊管理學系')
        code, _label = get_student_discipline(user)
        self.assertEqual(code, 'management')

    def test_no_department_returns_empty(self):
        user = self._user('')
        self.assertEqual(get_student_discipline(user), ('', ''))


class TutorContextTest(TestCase):
    """小老師背景包：注入系所、學群與對應課業知識"""

    def test_context_contains_dept_discipline_and_knowledge(self):
        user = CustomUser.objects.create_user(
            email='tutor@test.com', password='pw', name='T'
        )
        make_profile(user)
        profile = user.student_profile
        profile.department = '資訊工程學系'
        profile.save()

        context = build_tutor_context(user, 'zh-hant')
        self.assertIn('資訊工程學系', context)          # 系所
        self.assertIn('資訊學群', context)              # 學群
        self.assertIn('資料結構', context)              # 該學群知識包內容
        self.assertIn('加退選', context)                # 通用選課知識

    def test_no_profile_returns_empty(self):
        user = CustomUser.objects.create_user(
            email='noprof@test.com', password='pw', name='N'
        )
        self.assertEqual(build_tutor_context(user), '')


class KnowledgeAudienceFilterTest(TestCase):
    """知識庫適用對象過濾：學生只能檢索到自己學校 / 國籍 / 通用的內容"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='aud@test.com', password='pw', name='A'
        )
        # 越南籍、就讀中央大學的外籍生
        make_profile(self.user)

        ChatKnowledge.objects.create(
            category='admission', university='NCU',
            title='中央大學入學申請', keywords='入學申請',
            content='中央大學外籍生採單獨招生。',
        )
        ChatKnowledge.objects.create(
            category='admission', university='NTU',
            title='臺灣大學入學申請', keywords='入學申請',
            content='臺灣大學外籍生採線上申請系統。',
        )
        ChatKnowledge.objects.create(
            category='admission',
            title='入學申請通則', keywords='入學申請',
            content='所有學校都需要繳交畢業證書。',
        )

    def test_other_school_entry_excluded(self):
        items = search_knowledge_items('入學申請', user=self.user, limit=10)
        titles = [i.title for i in items]
        self.assertIn('中央大學入學申請', titles)
        self.assertIn('入學申請通則', titles)      # 通用內容仍要撈得到
        self.assertNotIn('臺灣大學入學申請', titles)

    def test_own_school_ranked_first(self):
        items = search_knowledge_items('入學申請', user=self.user, limit=10)
        self.assertEqual(items[0].title, '中央大學入學申請')

    def test_country_specific_entry_excluded(self):
        ChatKnowledge.objects.create(
            category='visa', country='Japan',
            title='日本籍簽證', keywords='簽證', content='日本護照免簽入境。',
        )
        ChatKnowledge.objects.create(
            category='visa', country='Vietnam',
            title='越南籍簽證', keywords='簽證', content='越南學生須先辦居留簽證。',
        )
        titles = [i.title for i in search_knowledge_items('簽證', user=self.user, limit=10)]
        self.assertIn('越南籍簽證', titles)
        self.assertNotIn('日本籍簽證', titles)

    def test_no_profile_keeps_all_entries(self):
        """沒填個人資料時不過濾，維持原本行為"""
        stranger = CustomUser.objects.create_user(
            email='stranger@test.com', password='pw', name='S'
        )
        titles = [i.title for i in search_knowledge_items('入學申請', user=stranger, limit=10)]
        self.assertIn('臺灣大學入學申請', titles)


class SchoolContextTest(TestCase):
    """校務資料包：讓「校長室在哪裡」可以依個人資料直接定位回答"""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='school@test.com', password='pw', name='S'
        )
        make_profile(self.user)
        school = School.objects.create(
            code='NCU',
            name='國立中央大學',
            aliases='中央,中大,NCU',
            address='320317 桃園市中壢區中大路 300 號',
            main_tel='03-4227151',
        )
        SchoolUnit.objects.create(
            school=school, name='校長室', aliases='校長辦公室',
            location='行政大樓 2 樓', ext='57000',
        )

    def test_context_contains_unit_location(self):
        context = build_school_context(self.user, 'zh-hant')
        self.assertIn('國立中央大學', context)
        self.assertIn('中大', context)                    # 簡稱
        self.assertIn('校長室', context)
        self.assertIn('行政大樓 2 樓', context)           # 位置
        self.assertIn('57000', context)                   # 分機

    def test_unverified_school_is_flagged(self):
        """last_verified_at 留空時必須提醒 AI 請學生再確認，避免直接當成事實"""
        self.assertIn('尚未經人工查核', build_school_context(self.user, 'zh-hant'))

    def test_no_school_record_returns_empty(self):
        School.objects.all().delete()
        self.assertEqual(build_school_context(self.user, 'zh-hant'), '')


class SeedKnowledgeCommandTest(TestCase):
    """seed_knowledge：從 knowledge_data 載入知識庫，且可重複執行"""

    def setUp(self):
        call_command('seed_schools', verbosity=0)   # schools 模組依賴 School 資料
        call_command('seed_knowledge', verbosity=0)

    def test_visa_entries_are_per_country(self):
        vn = ChatKnowledge.objects.get(category='visa', country='Vietnam')
        jp = ChatKnowledge.objects.get(category='visa', country='Japan')

        # 越南無免簽 → 必須說「須事先申請簽證」
        self.assertIn('須事先申請簽證', vn.content)
        # 日本有免簽 → 必須出現「免簽入境不能改辦居留簽證」的警告
        self.assertIn('不得在臺灣境內改辦居留簽證', jp.content)
        # 越南要分河內／胡志明市送件
        self.assertIn('胡志明市', vn.content)

    def test_unified_entries_have_no_audience(self):
        """財力／語言證明是統一回答，不可綁定學校或國籍"""
        for category in ('financial_proof', 'language_proof'):
            entry = ChatKnowledge.objects.get(category=category)
            self.assertEqual(entry.university, '')
            self.assertEqual(entry.country, '')

    def test_admission_split_by_identity(self):
        identities = set(
            ChatKnowledge.objects.filter(category='admission')
            .values_list('identity_type', flat=True)
        )
        self.assertEqual(
            identities, {'overseas_chinese', 'foreign_student', 'hong_kong_macau'}
        )

    def test_school_info_entries_carry_source_and_verified_date(self):
        ncu = ChatKnowledge.objects.get(category='school_info', university='NCU')
        self.assertIn('03-4227151', ncu.content)
        self.assertIn('57085', ncu.content)
        self.assertTrue(ncu.source_url)
        self.assertIsNotNone(ncu.last_verified_at)

    def test_rerun_is_idempotent(self):
        before = ChatKnowledge.objects.count()
        call_command('seed_knowledge', verbosity=0)
        self.assertEqual(ChatKnowledge.objects.count(), before)

    def test_vietnamese_student_gets_own_visa_entry_only(self):
        """端到端：越南學生問簽證，只撈到越南的，撈不到日本的"""
        user = CustomUser.objects.create_user(
            email='vnstudent@test.com', password='pw', name='V'
        )
        make_profile(user)   # 越南籍、中央大學、外籍生

        titles = [i.title for i in search_knowledge_items('簽證怎麼辦', user=user, limit=10)]
        self.assertTrue(any('越南' in t for t in titles))
        self.assertFalse(any('日本' in t for t in titles))


class WeatherQueryDetectionTest(TestCase):
    """天氣意圖偵測：中英文關鍵字都要能命中，不相關問題不誤判"""

    def test_detects_chinese_weather_keywords(self):
        for q in ['今天天氣如何', '會不會下雨', '溫度幾度', '要不要帶傘', '有颱風嗎']:
            self.assertTrue(detect_weather_query(q), f'未偵測到天氣問題: {q}')

    def test_detects_english_weather_keywords(self):
        for q in ['What is the weather today?', 'Is it going to rain?', 'Any typhoon?']:
            self.assertTrue(detect_weather_query(q), f'未偵測到天氣問題: {q}')

    def test_unrelated_question_not_flagged(self):
        self.assertFalse(detect_weather_query('居留證要怎麼辦？'))

    def test_empty_question_not_flagged(self):
        self.assertFalse(detect_weather_query(''))


class StudentCountyTest(TestCase):
    """學校 → 縣市對照：供天氣查詢使用"""

    def test_known_university_maps_to_county(self):
        user = CustomUser.objects.create_user(email='ncu_c@test.com', password='pw', name='C')
        make_profile(user, university='NCU')
        self.assertEqual(get_student_county(user), '桃園市')

    def test_multi_campus_university_maps_to_main_county(self):
        user = CustomUser.objects.create_user(email='nycu_c@test.com', password='pw', name='C')
        make_profile(user, university='NYCU')
        self.assertEqual(get_student_county(user), '新竹市')

    def test_no_profile_returns_none(self):
        user = CustomUser.objects.create_user(email='noc@test.com', password='pw', name='C')
        self.assertIsNone(get_student_county(user))


class WeatherForecastFetchTest(TestCase):
    """中央氣象署天氣預報查詢：不設定金鑰或查詢失敗一律回傳 None，不可編造資料"""

    def _mock_response(self, payload):
        resp = MagicMock()
        resp.json.return_value = payload
        return resp

    def test_no_api_key_returns_none(self):
        with override_settings(CWA_API_KEY=''):
            self.assertIsNone(fetch_weather_forecast('臺北市'))

    def test_no_county_returns_none(self):
        with override_settings(CWA_API_KEY='test-key'):
            self.assertIsNone(fetch_weather_forecast(None))

    @override_settings(CWA_API_KEY='test-key')
    def test_successful_response_formats_forecast(self):
        payload = {
            'success': 'true',
            'records': {
                'location': [{
                    'locationName': '臺北市',
                    'weatherElement': [
                        {'elementName': 'Wx', 'time': [
                            {'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '多雲時晴'}},
                        ]},
                        {'elementName': 'PoP', 'time': [
                            {'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '20'}},
                        ]},
                        {'elementName': 'MinT', 'time': [
                            {'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '26'}},
                        ]},
                        {'elementName': 'MaxT', 'time': [
                            {'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '31'}},
                        ]},
                    ],
                }],
            },
        }
        with patch('chatbot.services._cwa_get', return_value=self._mock_response(payload)):
            result = fetch_weather_forecast('臺北市')

        self.assertIsNotNone(result)
        self.assertIn('臺北市', result)
        self.assertIn('多雲時晴', result)
        self.assertIn('26~31', result)
        self.assertIn('20%', result)

    @override_settings(CWA_API_KEY='test-key')
    def test_api_failure_returns_none(self):
        with patch('chatbot.services._cwa_get', return_value=self._mock_response({'success': 'false'})):
            self.assertIsNone(fetch_weather_forecast('臺北市'))

    @override_settings(CWA_API_KEY='test-key')
    def test_network_error_returns_none(self):
        with patch('chatbot.services._cwa_get', side_effect=Exception('timeout')):
            self.assertIsNone(fetch_weather_forecast('臺北市'))

    @override_settings(CWA_API_KEY='test-key')
    def test_county_not_in_response_returns_none(self):
        payload = {'success': 'true', 'records': {'location': [{'locationName': '高雄市', 'weatherElement': []}]}}
        with patch('chatbot.services._cwa_get', return_value=self._mock_response(payload)):
            self.assertIsNone(fetch_weather_forecast('臺北市'))


class TyphoonBulletinFetchTest(TestCase):
    """颱風警報查詢：沒有作用中颱風或查詢失敗回傳 None，不可用來斷定安全無虞"""

    def _mock_response(self, payload):
        resp = MagicMock()
        resp.json.return_value = payload
        return resp

    def test_no_api_key_returns_none(self):
        with override_settings(CWA_API_KEY=''):
            self.assertIsNone(fetch_typhoon_bulletin())

    @override_settings(CWA_API_KEY='test-key')
    def test_no_active_typhoon_returns_none(self):
        payload = {'records': {'tropicalCyclones': {'tropicalCyclone': []}}}
        with patch('chatbot.services._cwa_get', return_value=self._mock_response(payload)):
            self.assertIsNone(fetch_typhoon_bulletin())

    @override_settings(CWA_API_KEY='test-key')
    def test_active_typhoon_returns_bulletin_text(self):
        payload = {'records': {'tropicalCyclones': {'tropicalCyclone': [
            {'typhoonName': 'KROVANH'},
        ]}}}
        with patch('chatbot.services._cwa_get', return_value=self._mock_response(payload)):
            result = fetch_typhoon_bulletin()
        self.assertIsNotNone(result)
        self.assertIn('KROVANH', result)

    @override_settings(CWA_API_KEY='test-key')
    def test_network_error_returns_none(self):
        with patch('chatbot.services._cwa_get', side_effect=Exception('timeout')):
            self.assertIsNone(fetch_typhoon_bulletin())


@override_settings(OPENAI_API_KEY='test-key', CWA_API_KEY='test-key')
class WeatherWiringInFriendReplyTest(TestCase):
    """
    端到端：friend 模式問天氣時，回覆內容附上真實查到的天氣資料。
    Mock 掉 OpenAI 呼叫本身，只驗證天氣資料有沒有正確接進回傳結果，不花真正的 API 費用。
    """

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='weather_e2e@test.com', password='pw', name='W'
        )
        make_profile(self.user, university='NCU')

    def _mock_openai(self):
        # generate_ai_reply 在函式內才 `from openai import OpenAI`，
        # 所以要 patch openai 模組本身的類別，而不是 chatbot.services.OpenAI
        fake_response = MagicMock()
        fake_response.output_text = '幫你查到天氣資訊囉！'
        fake_client = MagicMock()
        fake_client.responses.create.return_value = fake_response
        return patch('openai.OpenAI', return_value=fake_client)

    def test_weather_results_text_present_when_forecast_available(self):
        payload = {
            'success': 'true',
            'records': {'location': [{
                'locationName': '桃園市',
                'weatherElement': [
                    {'elementName': 'Wx', 'time': [{'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '晴天'}}]},
                    {'elementName': 'PoP', 'time': [{'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '10'}}]},
                    {'elementName': 'MinT', 'time': [{'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '27'}}]},
                    {'elementName': 'MaxT', 'time': [{'startTime': '2026-07-29T18:00:00+08:00', 'parameter': {'parameterName': '33'}}]},
                ],
            }]},
        }
        resp = MagicMock()
        resp.json.return_value = payload

        with patch('chatbot.services._cwa_get', return_value=resp), self._mock_openai():
            result = generate_ai_reply(
                user=self.user, question='今天天氣如何？',
                recent_messages=[], ai_mode='friend',
            )

        self.assertIn('weather_results_text', result)
        self.assertIsNotNone(result['weather_results_text'])
        self.assertIn('桃園市', result['weather_results_text'])
        self.assertIn('晴天', result['weather_results_text'])

    def test_no_weather_results_for_unrelated_question(self):
        with self._mock_openai():
            result = generate_ai_reply(
                user=self.user, question='今天心情不太好',
                recent_messages=[], ai_mode='friend',
            )
        self.assertIsNone(result.get('weather_results_text'))

    def test_no_cwa_key_tells_student_instead_of_guessing(self):
        with override_settings(CWA_API_KEY=''), self._mock_openai() as mock_openai:
            generate_ai_reply(
                user=self.user, question='今天天氣如何？',
                recent_messages=[], ai_mode='friend',
            )
        # 查不到資料時，instructions 必須明確禁止 AI 自己編造溫度／降雨機率
        instructions = mock_openai.return_value.responses.create.call_args.kwargs.get('instructions', '')
        input_text = mock_openai.return_value.responses.create.call_args.kwargs.get('input', '')
        combined = instructions + str(input_text)
        self.assertIn('不可以自己編造溫度', combined)


class CrossDomainDetectionTest(TestCase):
    """兩個 AI 管轄範圍的偵測邏輯：friend 專長關鍵字、helper 專屬知識庫命中"""

    def test_detects_chinese_friend_domain_keywords(self):
        for q in ['我今天心情不太好', '好想家', '室友吵架怎麼辦', '壓力好大']:
            self.assertTrue(detect_friend_domain_query(q), f'未偵測到情緒陪伴需求: {q}')

    def test_detects_english_friend_domain_keywords(self):
        for q in ['I feel so homesick', 'I need to vent about something']:
            self.assertTrue(detect_friend_domain_query(q), f'未偵測到情緒陪伴需求: {q}')

    def test_administrative_question_not_flagged_as_friend_domain(self):
        self.assertFalse(detect_friend_domain_query('簽證要怎麼辦？'))

    def test_empty_question_not_flagged(self):
        self.assertFalse(detect_friend_domain_query(''))

    def test_helper_only_knowledge_hit_detected(self):
        ChatKnowledge.objects.create(
            category='visa', bot_type='helper',
            title='越南籍簽證怎麼辦', keywords='簽證',
            content='越南學生須先辦居留簽證。',
        )
        self.assertTrue(detect_helper_domain_hit('簽證怎麼辦'))

    def test_shared_both_knowledge_not_treated_as_helper_exclusive(self):
        ChatKnowledge.objects.create(
            category='emergency', bot_type='both',
            title='緊急聯絡電話', keywords='緊急',
            content='119 緊急醫療救護專線。',
        )
        self.assertFalse(detect_helper_domain_hit('緊急'))

    def test_no_matching_knowledge_returns_false(self):
        self.assertFalse(detect_helper_domain_hit('完全查不到的關鍵字xyz123'))


@override_settings(OPENAI_API_KEY='test-key')
class CrossDomainWiringTest(TestCase):
    """
    端到端：friend 模式問到 helper 專長問題、helper 模式問到 friend 專長問題時，
    prompt 裡都要出現對應的「任務歸屬提醒」，引導 AI 建議學生切換模式。
    Mock 掉 OpenAI 呼叫本身，只檢查傳給模型的 instructions／input 內容。
    """

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='crossdomain@test.com', password='pw', name='X'
        )
        make_profile(self.user)

    def _mock_openai(self):
        fake_response = MagicMock()
        fake_response.output_text = '好的！'
        fake_client = MagicMock()
        fake_client.responses.create.return_value = fake_response
        return patch('openai.OpenAI', return_value=fake_client)

    def _prompt_text(self, mock_openai):
        call = mock_openai.return_value.responses.create.call_args
        instructions = call.kwargs.get('instructions', '')
        input_text = call.kwargs.get('input', '')
        return instructions + str(input_text)

    def test_friend_mode_hints_helper_domain_on_visa_question(self):
        ChatKnowledge.objects.create(
            category='visa', bot_type='helper', university='',
            title='越南籍簽證怎麼辦', keywords='簽證',
            content='越南學生須先辦居留簽證，請洽駐外館處。',
        )
        with self._mock_openai() as mock_openai:
            generate_ai_reply(
                user=self.user, question='簽證要怎麼辦？',
                recent_messages=[], ai_mode='friend',
            )
        self.assertIn('任務歸屬提醒', self._prompt_text(mock_openai))
        self.assertIn('ReadyTo 任務小幫手', self._prompt_text(mock_openai))

    def test_friend_mode_no_hint_for_casual_chat(self):
        with self._mock_openai() as mock_openai:
            generate_ai_reply(
                user=self.user, question='今天天氣很好，想出去走走',
                recent_messages=[], ai_mode='friend',
            )
        self.assertNotIn('任務歸屬提醒', self._prompt_text(mock_openai))

    def test_helper_mode_hints_friend_domain_when_nothing_else_matches(self):
        with self._mock_openai() as mock_openai:
            generate_ai_reply(
                user=self.user, question='我今天心情很不好，好想家',
                recent_messages=[], ai_mode='helper',
            )
        prompt = self._prompt_text(mock_openai)
        self.assertIn('任務歸屬提醒', prompt)
        self.assertIn('ReadyTo 聊天好朋友', prompt)

    def test_helper_mode_crisis_message_takes_priority_over_domain_hint(self):
        """危機訊息即使也帶有情緒字眼，也要走危機求助流程，不是單純建議切換模式"""
        with self._mock_openai() as mock_openai:
            generate_ai_reply(
                user=self.user, question='我好想家，好難過，不想活了',
                recent_messages=[], ai_mode='helper',
            )
        prompt = self._prompt_text(mock_openai)
        self.assertIn('危機求助資源', prompt)
        self.assertIn('自傷', prompt)
        # 危機優先權更高：不應該只丟一句「切換到聊天好朋友」就打發掉
        self.assertNotIn('任務歸屬提醒', prompt)
