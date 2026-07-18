from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from chatbot.models import ChatKnowledge, ChatSession, ChatMessage, ChatFeedback
from chatbot.services import (
    build_local_personal_answer,
    build_tutor_context,
    contains_crisis_keywords,
    detect_question_language,
    generate_ai_reply,
    get_role_instructions,
    get_student_discipline,
)
from users.models import CustomUser, StudentProfile


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
