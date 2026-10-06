from datetime import date, datetime, timedelta
from io import StringIO
from types import SimpleNamespace
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from chatbot.models import ChatMessage, ChatSession
from flows.models import FlowStage, Reminder, StudentTask, Task
from users.models import CustomUser, StudentProfile

from . import ask, metrics, services
from .alerts import compute_alerts, high_risk_groups
from .build import build_snapshot, student_key
from .classify import classify_pending
from .models import (
    DimStudent, FactQuestion, FactStudentTask, InsightAlert, InsightAskLog, QuestionClassification,
    StaffAccess, StaffProfile,
)
from .question_categories import classify_by_rules, mask_pii
from .task_categories import classify_task

SNAPSHOT = date(2026, 10, 1)


def make_student(email, university='NTU', identity='foreign_student', nationality='Vietnam',
                 arrival=None, **user_kwargs):
    user = CustomUser.objects.create_user(email=email, password='pw', name='Test', **user_kwargs)
    return StudentProfile.objects.create(
        user=user,
        nationality=nationality,
        university=university,
        identity_type=identity,
        admission_status='arrived',
        expected_arrival=arrival,
    )


def make_fact(**kwargs):
    defaults = dict(
        snapshot_date=SNAPSHOT, student_key='k', university='NTU', nationality='Vietnam',
        identity_type='foreign_student', arrival_cohort='2026-09', academic_year=115,
        task_category='residence_permit', is_required=True, has_deadline=True,
        due_date=SNAPSHOT - timedelta(days=5), status='completed', completed_date=None,
        is_completed=True, is_due=True, is_overdue_open=False, is_overdue_late=False,
        is_overdue=False, is_possibly_unreported=False, reminder_count=0,
    )
    defaults.update(kwargs)
    return FactStudentTask(**defaults)


class TaskCategoryTest(TestCase):
    def setUp(self):
        self.stage = FlowStage.objects.create(name='抵台後', order=1)

    def task(self, title, code='', title_en=''):
        return Task(stage=self.stage, title=title, task_code=code, title_en=title_en)

    def test_resident_visa_is_entry_permit_not_residence(self):
        self.assertEqual(classify_task(self.task('申請居留簽證')), 'entry_permit')

    def test_hk_macau_residence_entry_permit_is_residence(self):
        self.assertEqual(classify_task(self.task('辦理臺灣地區居留入出境證')), 'residence_permit')

    def test_arc(self):
        self.assertEqual(classify_task(self.task('申請居留證', title_en='Apply for ARC')), 'residence_permit')

    def test_course_enrollment_is_course(self):
        self.assertEqual(classify_task(self.task('選課', title_en='Course enrollment')), 'course')

    def test_registration(self):
        self.assertEqual(classify_task(self.task('新生報到')), 'registration')

    def test_task_code_map_wins(self):
        self.assertEqual(classify_task(self.task('隨便的標題', code='apply_nhi')), 'nhi')

    def test_unknown_is_other(self):
        self.assertEqual(classify_task(self.task('開銀行帳戶')), 'other')

    def test_real_task_codes(self):
        self.assertEqual(classify_task(self.task('繳交學雜費', code='pay_tuition_and_fees')), 'registration')
        self.assertEqual(classify_task(self.task('中文能力分級測驗', code='delayed_chinese_placement')), 'course')
        self.assertEqual(classify_task(self.task('良民證', code='police_clearance')), 'other')


class QuestionRuleTest(TestCase):
    def test_rules(self):
        self.assertEqual(classify_by_rules('How do I apply for an ARC?'), 'residence_permit')
        self.assertEqual(classify_by_rules('健保什麼時候可以加保？'), 'nhi')
        self.assertEqual(classify_by_rules('居留簽證要準備什麼'), 'entry_permit')
        self.assertIsNone(classify_by_rules('hi'))

    def test_mask_pii(self):
        masked = mask_pii('my email is a.b@test.com, passport A12345678, phone 0912-345-678')
        self.assertNotIn('a.b@test.com', masked)
        self.assertNotIn('A12345678', masked)
        self.assertNotIn('0912-345-678', masked)


class MetricsTest(TestCase):
    def test_make_rate_suppresses_small_n(self):
        self.assertTrue(metrics.make_rate(3, 9)['suppressed'])
        self.assertIsNone(metrics.make_rate(3, 9)['rate'])
        self.assertEqual(metrics.make_rate(3, 10)['rate'], 30.0)

    def test_academic_year(self):
        self.assertEqual(metrics.academic_year_of(date(2026, 9, 1)), 115)
        self.assertEqual(metrics.academic_year_of(date(2026, 7, 31)), 114)

    def test_completion_rate_only_counts_due_tasks(self):
        facts = [make_fact() for _ in range(8)]
        facts += [make_fact(status='not_started', is_completed=False, is_overdue_open=True, is_overdue=True)
                  for _ in range(2)]
        # 未到期、未完成：不應拉低完成率
        facts += [make_fact(status='not_started', is_completed=False, is_due=False) for _ in range(20)]
        # 選填任務不計入
        facts += [make_fact(is_required=False, status='not_started', is_completed=False) for _ in range(20)]
        FactStudentTask.objects.bulk_create(facts)
        summary = metrics.task_summary(FactStudentTask.objects.all())
        self.assertEqual(summary['completion']['rate'], 80.0)
        self.assertEqual(summary['completion']['n'], 10)
        self.assertEqual(summary['overdue']['rate'], 20.0)

    def test_distribution_merges_small_groups(self):
        rows = [DimStudent(snapshot_date=SNAPSHOT, student_key=f'v{i}', university='NTU', nationality='Vietnam',
                           identity_type='foreign_student', admission_status='arrived') for i in range(12)]
        rows += [DimStudent(snapshot_date=SNAPSHOT, student_key=f'm{i}', university='NTU', nationality='Mongolia',
                            identity_type='foreign_student', admission_status='arrived') for i in range(3)]
        DimStudent.objects.bulk_create(rows)
        dist = metrics.distribution(DimStudent.objects.all(), 'nationality')
        labels = [r['label'] for r in dist]
        self.assertNotIn('蒙古', labels)
        self.assertEqual(dist[-1]['value'], '_other')
        self.assertEqual(dist[-1]['count'], 3)


class AlertTest(TestCase):
    def _facts(self, academic_year, cohort, n, overdue, **kwargs):
        return [
            make_fact(academic_year=academic_year, arrival_cohort=cohort,
                      is_overdue=i < overdue, is_overdue_open=i < overdue, **kwargs)
            for i in range(n)
        ]

    def test_yoy_alert_triggers(self):
        FactStudentTask.objects.bulk_create(
            self._facts(114, '2025-09', 40, 3) + self._facts(115, '2026-09', 40, 8)
        )
        alerts = compute_alerts(FactStudentTask.objects.all())
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert['task_category'], 'residence_permit')
        self.assertEqual(alert['baseline_type'], 'yoy')
        self.assertEqual(alert['current_rate'], 20.0)
        self.assertEqual(alert['baseline_rate'], 7.5)
        self.assertEqual(alert['delta_pp'], 12.5)
        self.assertIn('上升 12.5 個百分點', alert['recommendation'])

    def test_no_alert_when_sample_too_small(self):
        FactStudentTask.objects.bulk_create(
            self._facts(114, '2025-09', 40, 3) + self._facts(115, '2026-09', 20, 8)
        )
        self.assertEqual(compute_alerts(FactStudentTask.objects.all()), [])

    def test_reminder_effect_mentioned_only_when_gap_is_meaningful(self):
        base = self._facts(114, '2025-09', 40, 3)
        # 本期：有提醒 20 筆逾期 4（20%）、沒提醒 20 筆逾期 5（25%）→ 差 5 個百分點，應提及
        current = (self._facts(115, '2026-09', 20, 4, reminder_count=1)
                   + self._facts(115, '2026-09', 20, 5))
        FactStudentTask.objects.bulk_create(base + current)
        self.assertIn('到期前收到提醒', compute_alerts(FactStudentTask.objects.all())[0]['recommendation'])

        FactStudentTask.objects.all().delete()
        # 有提醒 20%、沒提醒 22.7% → 差距不到 3 個百分點，不應提及
        current = (self._facts(115, '2026-09', 20, 4, reminder_count=1)
                   + self._facts(115, '2026-09', 22, 5))
        FactStudentTask.objects.bulk_create(base + current)
        self.assertNotIn('到期前收到提醒', compute_alerts(FactStudentTask.objects.all())[0]['recommendation'])

    def test_no_alert_when_change_too_small(self):
        FactStudentTask.objects.bulk_create(
            self._facts(114, '2025-09', 100, 10) + self._facts(115, '2026-09', 100, 12)
        )
        self.assertEqual(compute_alerts(FactStudentTask.objects.all()), [])


class BuildSnapshotTest(TestCase):
    def setUp(self):
        stage = FlowStage.objects.create(name='抵台後', order=1)
        self.arc = Task.objects.create(stage=stage, title='申請居留證', task_code='apply_arc',
                                       deadline_type='from_arrival', deadline_days=15, order=1)
        self.nhi = Task.objects.create(stage=stage, title='加入健保', task_code='apply_nhi',
                                       deadline_type='from_arrival', deadline_days=190, order=2)
        self.bank = Task.objects.create(stage=stage, title='開銀行帳戶', order=3)
        self.reg = Task.objects.create(stage=stage, title='新生報到',
                                       deadline_type='absolute', deadline_date=SNAPSHOT - timedelta(days=20), order=4)

        arrival = SNAPSHOT - timedelta(days=60)
        self.student = make_student('s1@uni.edu', arrival=arrival)
        StudentTask.objects.create(student=self.student, task=self.arc, status='not_started')
        StudentTask.objects.create(student=self.student, task=self.nhi, status='not_started')
        StudentTask.objects.create(student=self.student, task=self.bank, status='completed',
                                   completed_at=timezone.now())
        late = timezone.make_aware(datetime.combine(SNAPSHOT - timedelta(days=10), datetime.min.time()))
        self.reg_st = StudentTask.objects.create(student=self.student, task=self.reg, status='completed',
                                                 completed_at=late)
        Reminder.objects.create(student=self.student, student_task=self.reg_st, message='x', kind='due_soon')

        # 不應納入統計的帳號
        make_student('admin@uni.edu', role='admin')
        make_student('staffflag@uni.edu', is_staff=True)
        staff_with_profile = make_student('staff@uni.edu')
        StaffProfile.objects.create(user=staff_with_profile.user, university='NTU', powerbi_upn='Staff@school.edu.tw')
        make_student('tester@example.com')

    def build(self):
        with mock.patch.dict('os.environ', {'INSIGHTS_EXCLUDED_EMAIL_DOMAINS': 'example.com'}):
            return build_snapshot(SNAPSHOT)

    def fact(self, category):
        return FactStudentTask.objects.get(task_category=category)

    def test_excludes_admin_staff_and_test_accounts(self):
        summary = self.build()
        self.assertEqual(summary['students'], 1)
        self.assertEqual(DimStudent.objects.count(), 1)

    def test_student_key_is_hashed(self):
        self.build()
        key = DimStudent.objects.get().student_key
        self.assertEqual(key, student_key(self.student.id))
        self.assertNotEqual(key, str(self.student.id))
        self.assertEqual(len(key), 32)

    def test_overdue_open(self):
        self.build()
        arc = self.fact('residence_permit')
        self.assertTrue(arc.is_due)
        self.assertTrue(arc.is_overdue_open)
        self.assertTrue(arc.is_overdue)
        # 從未登入 → 可能未回報
        self.assertTrue(arc.is_possibly_unreported)

    def test_not_yet_due(self):
        self.build()
        nhi = self.fact('nhi')
        self.assertTrue(nhi.has_deadline)
        self.assertFalse(nhi.is_due)
        self.assertFalse(nhi.is_overdue)

    def test_no_deadline(self):
        self.build()
        bank = self.fact('other')
        self.assertFalse(bank.has_deadline)
        self.assertFalse(bank.is_due)

    def test_late_completion_and_reminder_count(self):
        self.build()
        reg = self.fact('registration')
        self.assertTrue(reg.is_overdue_late)
        self.assertFalse(reg.is_overdue_open)
        self.assertEqual(reg.reminder_count, 1)

    def test_reports_unmapped_tasks(self):
        summary = self.build()
        self.assertEqual([t['title'] for t in summary['unmapped_tasks']], ['開銀行帳戶'])

    def test_questions_only_from_helper_mode(self):
        helper = ChatSession.objects.create(user=self.student.user, ai_mode='helper')
        friend = ChatSession.objects.create(user=self.student.user, ai_mode='friend')
        m1 = ChatMessage.objects.create(session=helper, role='user', content='ARC 怎麼辦')
        m2 = ChatMessage.objects.create(session=friend, role='user', content='我好焦慮')
        QuestionClassification.objects.create(message=m1, category='residence_permit', method='rule')
        QuestionClassification.objects.create(message=m2, category='other', method='rule')
        self.build()
        self.assertEqual(list(FactQuestion.objects.values_list('category', flat=True)), ['residence_permit'])

    def test_analytics_tables_have_no_pii_columns(self):
        forbidden = {'name', 'email', 'content', 'note', 'avatar', 'department', 'last_login_ip'}
        for model in (DimStudent, FactStudentTask, FactQuestion, InsightAlert):
            columns = {f.name for f in model._meta.get_fields()}
            self.assertFalse(columns & forbidden, model.__name__)

    def test_staff_access_table_for_powerbi_rls(self):
        self.build()
        self.assertEqual(list(StaffAccess.objects.values_list('powerbi_upn', 'university')),
                         [('staff@school.edu.tw', 'NTU')])

    def test_rebuild_keeps_demo_rows(self):
        DimStudent.objects.create(snapshot_date=SNAPSHOT, student_key='demo', university='NTU', nationality='Japan',
                                  identity_type='foreign_student', admission_status='arrived', is_demo=True)
        self.build()
        self.build()
        self.assertEqual(DimStudent.objects.filter(is_demo=True).count(), 1)
        self.assertEqual(DimStudent.objects.filter(is_demo=False).count(), 1)


class ClassifyQuestionsTest(TestCase):
    def setUp(self):
        self.student = make_student('s@uni.edu')
        self.helper = ChatSession.objects.create(user=self.student.user, ai_mode='helper')

    def msg(self, content, session=None, role='user'):
        return ChatMessage.objects.create(session=session or self.helper, role=role, content=content)

    def test_rules_without_llm(self):
        arc = self.msg('How to apply ARC?')
        hi = self.msg('hi')
        self.msg('回覆', role='assistant')
        friend = ChatSession.objects.create(user=self.student.user, ai_mode='friend')
        self.msg('ARC 好煩', session=friend)

        stats = classify_pending(use_llm=False)
        self.assertEqual(stats['rule'], 1)
        self.assertEqual(stats['none'], 1)
        self.assertEqual(QuestionClassification.objects.get(message=arc).category, 'residence_permit')
        self.assertEqual(QuestionClassification.objects.get(message=hi).category, 'other')
        self.assertEqual(QuestionClassification.objects.count(), 2)

    def test_llm_fallback(self):
        msg = self.msg('Tôi cần làm thẻ cư trú ở đâu?')
        client = mock.Mock()
        client.responses.create.return_value = SimpleNamespace(output_text='["residence_permit"]')
        stats = classify_pending(use_llm=True, client=client)
        self.assertEqual(stats['llm'], 1)
        self.assertEqual(QuestionClassification.objects.get(message=msg).method, 'llm')

    def test_llm_failure_retries_next_run(self):
        self.msg('Tôi cần làm thẻ cư trú ở đâu?')
        client = mock.Mock()
        client.responses.create.side_effect = RuntimeError('down')
        stats = classify_pending(use_llm=True, client=client)
        self.assertEqual(stats['llm_failed'], 1)
        self.assertEqual(QuestionClassification.objects.count(), 0)


class PermissionTest(TestCase):
    def setUp(self):
        # 不受本機 .env 的 INSIGHTS_USE_DEMO_DATA 影響
        patcher = mock.patch.dict('os.environ', {'INSIGHTS_USE_DEMO_DATA': 'False'})
        patcher.start()
        self.addCleanup(patcher.stop)
        DimStudent.objects.bulk_create(
            [DimStudent(snapshot_date=SNAPSHOT, student_key=f'ntu{i}', university='NTU', nationality='Japan',
                        identity_type='foreign_student', admission_status='arrived') for i in range(12)]
            + [DimStudent(snapshot_date=SNAPSHOT, student_key=f'nccu{i}', university='NCCU', nationality='Japan',
                          identity_type='foreign_student', admission_status='arrived') for i in range(5)]
        )
        self.url = reverse('insights:dashboard')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_student_forbidden(self):
        student = make_student('s@uni.edu')
        self.client.force_login(student.user)
        for name in ('dashboard', 'tasks', 'alerts', 'questions'):
            self.assertEqual(self.client.get(reverse(f'insights:{name}')).status_code, 403)

    def test_staff_sees_only_own_school(self):
        user = CustomUser.objects.create_user(email='staff@ntu.edu.tw', password='pw', name='Staff')
        StaffProfile.objects.create(user=user, university='NTU')
        self.client.force_login(user)
        response = self.client.get(self.url, {'school': 'NCCU'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['overview']['total'], 12)

    def test_inactive_staff_forbidden(self):
        user = CustomUser.objects.create_user(email='old@ntu.edu.tw', password='pw', name='Old')
        StaffProfile.objects.create(user=user, university='NTU', is_active=False)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_sees_all_and_can_filter_school(self):
        admin = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='Admin', role='admin')
        self.client.force_login(admin)
        self.assertEqual(self.client.get(self.url).context['overview']['total'], 17)
        self.assertEqual(self.client.get(self.url, {'school': 'NCCU'}).context['overview']['total'], 5)

    def test_all_pages_render_for_admin(self):
        admin = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='Admin', role='admin')
        self.client.force_login(admin)
        for name in ('dashboard', 'tasks', 'alerts', 'questions'):
            self.assertEqual(self.client.get(reverse(f'insights:{name}')).status_code, 200, name)


class SeedDemoTest(TestCase):
    def test_seed_produces_planted_alert_and_clear_removes_it(self):
        call_command('seed_insights_demo', students=800, stdout=StringIO())
        self.assertTrue(DimStudent.objects.filter(is_demo=True).exists())
        self.assertTrue(InsightAlert.objects.filter(is_demo=True, university='ALL',
                                                    task_category='residence_permit').exists())
        call_command('seed_insights_demo', clear=True, stdout=StringIO())
        self.assertFalse(DimStudent.objects.filter(is_demo=True).exists())

    def test_dashboard_shows_demo_banner(self):
        call_command('seed_insights_demo', students=300, stdout=StringIO())
        admin = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='Admin', role='admin')
        self.client.force_login(admin)
        with mock.patch.dict('os.environ', {'INSIGHTS_USE_DEMO_DATA': 'True'}):
            response = self.client.get(reverse('insights:dashboard'))
        self.assertContains(response, '示範資料')
        self.assertEqual(response.context['overview']['total'], 300)


# ══════════════════════════════════════════
# v1.3：期間比較、AI 資料助理、CSV 匯出
# ══════════════════════════════════════════
class RealDataMixin:
    """不受本機 .env 的 INSIGHTS_USE_DEMO_DATA 影響。"""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict('os.environ', {'INSIGHTS_USE_DEMO_DATA': 'False'})
        patcher.start()
        self.addCleanup(patcher.stop)


def overdue_facts(n, overdue, **kwargs):
    return [make_fact(is_overdue=i < overdue, is_overdue_open=i < overdue, **kwargs) for i in range(n)]


class ComparePeriodsTest(TestCase):
    def test_uses_academic_year_and_sorts_most_improved_first(self):
        FactStudentTask.objects.bulk_create(
            overdue_facts(20, 4, academic_year=114, arrival_cohort='2025-09')
            + overdue_facts(20, 2, academic_year=115, arrival_cohort='2026-09')
            + overdue_facts(20, 1, task_category='nhi', academic_year=114, arrival_cohort='2025-09')
            + overdue_facts(20, 5, task_category='nhi', academic_year=115, arrival_cohort='2026-09')
        )
        rows = metrics.compare_periods(FactStudentTask.objects.all())
        first = rows[0]
        self.assertEqual(first['value'], 'residence_permit')
        self.assertEqual(first['period_type'], 'academic_year')
        self.assertEqual(first['delta_pp'], -10.0)
        self.assertEqual(rows[1]['value'], 'nhi')
        self.assertEqual(rows[1]['delta_pp'], 20.0)
        # 沒有資料的分類排最後，無法比較
        self.assertIsNone(rows[-1]['delta_pp'])

    def test_falls_back_to_cohort_within_single_academic_year(self):
        FactStudentTask.objects.bulk_create(
            overdue_facts(10, 1, academic_year=115, arrival_cohort='2026-08')
            + overdue_facts(10, 3, academic_year=115, arrival_cohort='2026-09')
        )
        row = metrics.compare_periods(FactStudentTask.objects.all(), 'residence_permit')[0]
        self.assertEqual(row['period_type'], 'arrival_cohort')
        self.assertEqual(row['delta_pp'], 20.0)

    def test_small_periods_are_not_compared(self):
        FactStudentTask.objects.bulk_create(
            overdue_facts(9, 1, academic_year=114) + overdue_facts(20, 3, academic_year=115)
        )
        row = metrics.compare_periods(FactStudentTask.objects.all(), 'residence_permit')[0]
        self.assertIsNone(row['delta_pp'])


class HighRiskGroupsTest(TestCase):
    def test_finds_group_above_overall_with_enough_n(self):
        FactStudentTask.objects.bulk_create(
            overdue_facts(40, 20, nationality='Vietnam') + overdue_facts(40, 2, nationality='Japan')
        )
        result = high_risk_groups(FactStudentTask.objects.all())
        self.assertEqual(result['overall']['rate'], 27.5)
        self.assertEqual([(g['label'], g['rate'], g['n']) for g in result['groups']], [('越南籍', 50.0, 40)])


class AskToolTest(RealDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        FactStudentTask.objects.bulk_create(
            overdue_facts(12, 3, university='NTU') + overdue_facts(15, 15, university='NCCU')
        )

    def test_invalid_arguments_return_error(self):
        data = services.datasets('ALL', {})
        self.assertIn('error', ask.run_tool('task_metrics', {'group_by': 'email', 'task_category': None}, data))
        self.assertIn('error', ask.run_tool('drop_table', {}, data))
        self.assertIn('error', ask.run_tool('list_alerts', {'school': 'NCCU'}, data))

    def test_tools_only_see_scoped_school(self):
        data = services.datasets('NTU', {})
        result = ask.run_tool('task_metrics', {'group_by': 'task_category', 'task_category': None}, data)
        self.assertEqual(result['rows'], [{
            'value': 'residence_permit', 'label': '居留證件', 'completion_rate': 100.0,
            'overdue_rate': 25.0, 'n': 12, 'note': '',
        }])

    def test_tools_have_no_school_parameter(self):
        for tool in ask.TOOLS:
            self.assertNotIn('school', tool['parameters']['properties'])
            self.assertNotIn('university', tool['parameters']['properties'])


def fake_response(output_text='', function_calls=()):
    output = [SimpleNamespace(type='function_call', name=name, arguments=json_args, call_id=f'call{i}')
              for i, (name, json_args) in enumerate(function_calls)]
    return SimpleNamespace(output=output or [SimpleNamespace(type='message')], output_text=output_text)


CONTEXT = {'school_label': '國立臺灣大學（NTU）', 'filter_label': '無', 'snapshot_date': SNAPSHOT, 'is_demo': False}


class AskLLMTest(RealDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        FactStudentTask.objects.bulk_create(overdue_facts(40, 8))
        self.user = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='A', role='admin')
        self.data = services.datasets('ALL', {})

    def client_with(self, *responses):
        client = mock.Mock()
        client.responses.create.side_effect = list(responses)
        return client

    def test_tool_call_then_answer_is_verified(self):
        client = self.client_with(
            fake_response(function_calls=[('task_metrics', '{"group_by":"task_category","task_category":null}')]),
            fake_response('居留證件逾期率為 20.0%（n=40）。'),
        )
        result = ask.answer_question(self.user, 'ALL', self.data, CONTEXT, '哪個流程逾期最多？', client=client)
        self.assertEqual(result['source'], 'llm')
        self.assertTrue(result['verified'])
        self.assertEqual(result['calls'][0]['name'], 'task_metrics')
        second_input = client.responses.create.call_args_list[1].kwargs['input']
        self.assertEqual(second_input[-1]['type'], 'function_call_output')
        log = InsightAskLog.objects.get()
        self.assertEqual((log.source, log.verified), ('llm', True))

    def test_hallucinated_number_is_flagged(self):
        client = self.client_with(
            fake_response(function_calls=[('task_metrics', '{"group_by":"task_category","task_category":null}')]),
            fake_response('居留證件逾期率為 35.5%（n=40）。'),
        )
        result = ask.answer_question(self.user, 'ALL', self.data, CONTEXT, 'q', client=client)
        self.assertFalse(result['verified'])
        self.assertEqual(result['unverified'], ['35.5'])
        self.assertFalse(InsightAskLog.objects.get().verified)

    def test_too_many_tool_calls(self):
        calls = [('list_alerts', '{}')] * (ask.MAX_TOOL_CALLS + 1)
        client = self.client_with(fake_response(function_calls=calls))
        result = ask.answer_question(self.user, 'ALL', self.data, CONTEXT, 'q', client=client)
        self.assertEqual(result['answer'], ask.TOO_COMPLEX)

    def test_openai_error_falls_back(self):
        client = mock.Mock()
        client.responses.create.side_effect = RuntimeError('down')
        result = ask.answer_question(self.user, 'ALL', self.data, CONTEXT, 'q', client=client)
        self.assertEqual((result['source'], result['answer']), ('error', ask.AI_UNAVAILABLE))

    @override_settings(OPENAI_API_KEY='')
    def test_no_api_key(self):
        result = ask.answer_question(self.user, 'ALL', self.data, CONTEXT, 'q')
        self.assertEqual(result['answer'], ask.AI_UNAVAILABLE)
        self.assertFalse(ask.ai_available())

    def test_daily_quota(self):
        InsightAskLog.objects.bulk_create([
            InsightAskLog(user=self.user, scope='ALL', question='q', source='llm') for _ in range(ask.DAILY_LIMIT)
        ])
        InsightAskLog.objects.create(user=self.user, scope='ALL', question='q', source='preset')
        self.assertEqual(ask.remaining_quota(self.user), 0)


class AskPresetTest(TestCase):
    def setUp(self):
        call_command('seed_insights_demo', students=800, stdout=StringIO())
        self.user = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='A', role='admin')
        with mock.patch.dict('os.environ', {'INSIGHTS_USE_DEMO_DATA': 'True'}):
            self.data = services.datasets('ALL', {})

    def test_all_presets_answer_with_evidence(self):
        for preset in ask.PRESETS:
            result = ask.answer_preset(self.user, 'ALL', self.data, preset['id'])
            self.assertTrue(result['calls'], preset['question'])
            self.assertNotIn('資料不足', result['answer'], preset['question'])
            self.assertTrue(ask.verify_numbers(result['answer'], result['calls'])[0], result['answer'])
        self.assertEqual(InsightAskLog.objects.filter(source='preset').count(), 5)
        self.assertEqual(ask.remaining_quota(self.user), ask.DAILY_LIMIT)

    def test_planted_scenario_in_presets(self):
        answer = ask.answer_preset(self.user, 'ALL', self.data, 1)['answer']
        self.assertIn('外籍生', answer)


class AskViewTest(RealDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        FactStudentTask.objects.bulk_create(overdue_facts(40, 8))
        self.admin = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='A', role='admin')
        self.url = reverse('insights:ask')

    def test_student_forbidden(self):
        student = make_student('s@uni.edu')
        self.client.force_login(student.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'question': 'q'}).status_code, 403)

    def test_preset(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'preset': 2})
        self.assertContains(response, '居留證件')
        self.assertContains(response, '資料依據')

    @override_settings(OPENAI_API_KEY='test-key')
    def test_post_question(self):
        client = mock.Mock()
        client.responses.create.side_effect = [
            fake_response(function_calls=[('task_metrics', '{"group_by":"task_category","task_category":null}')]),
            fake_response('居留證件逾期率為 20.0%（n=40）。'),
        ]
        self.client.force_login(self.admin)
        with mock.patch('insights.ask.llm_client', return_value=client):
            response = self.client.post(self.url, {'question': '哪個流程逾期最多？'})
        self.assertContains(response, '居留證件逾期率為 20.0%（n=40）。')
        self.assertNotContains(response, '無法對應到資料的數字')

    @override_settings(OPENAI_API_KEY='test-key')
    def test_quota_exceeded_does_not_call_openai(self):
        InsightAskLog.objects.bulk_create([
            InsightAskLog(user=self.admin, scope='ALL', question='q', source='llm') for _ in range(ask.DAILY_LIMIT)
        ])
        self.client.force_login(self.admin)
        with mock.patch('insights.ask.llm_client') as factory:
            response = self.client.post(self.url, {'question': 'q'})
        factory.assert_not_called()
        self.assertContains(response, '已達上限')


class ExportTest(RealDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        FactStudentTask.objects.bulk_create(
            overdue_facts(12, 3, university='NTU', nationality='Vietnam')
            + overdue_facts(5, 1, university='NTU', nationality='Indonesia')
            + overdue_facts(12, 3, university='NCCU', nationality='Japan')
        )
        user = CustomUser.objects.create_user(email='staff@ntu.edu.tw', password='pw', name='Staff')
        StaffProfile.objects.create(user=user, university='NTU')
        self.client.force_login(user)

    def get(self, name):
        return self.client.get(reverse('insights:export', args=[name]))

    def test_tasks_csv_is_scoped_and_suppressed(self):
        response = self.get('tasks')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertTrue(content.startswith('﻿'))
        self.assertIn('請勿外流', content.splitlines()[0])
        self.assertIn('越南', content)
        self.assertNotIn('日本', content)          # 別校資料
        indonesia = next(line for line in content.splitlines() if '印尼' in line)
        self.assertIn('<10', indonesia)
        self.assertIn('樣本不足', indonesia)
        self.assertNotIn('student_key', content)

    def test_other_exports(self):
        self.assertEqual(self.get('questions').status_code, 200)
        self.assertEqual(self.get('alerts').status_code, 200)
        self.assertEqual(self.get('students').status_code, 404)

    def test_student_forbidden(self):
        student = make_student('s@uni.edu')
        self.client.force_login(student.user)
        self.assertEqual(self.get('tasks').status_code, 403)


class NavInsightsButtonTest(TestCase):
    """navbar 的 Insights 按鈕：只有能進 /insights/ 的人看得到。"""
    BUTTON = 'id="navInsightsBtn"'

    def page(self, user=None):
        if user:
            self.client.force_login(user)
        return self.client.get(reverse('faq_page'))

    def test_hidden_for_anonymous(self):
        self.assertNotContains(self.page(), self.BUTTON)

    def test_hidden_for_student(self):
        self.assertNotContains(self.page(make_student('s@uni.edu').user), self.BUTTON)

    def test_hidden_for_user_without_profile(self):
        user = CustomUser.objects.create_user(email='new@uni.edu', password='pw', name='New')
        self.assertNotContains(self.page(user), self.BUTTON)

    def test_hidden_for_django_staff_flag_only(self):
        # is_staff 只代表能進 Django Admin，不等於能看 insights
        user = CustomUser.objects.create_user(email='ops@readyto.tw', password='pw', name='Ops', is_staff=True)
        self.assertNotContains(self.page(user), self.BUTTON)

    def test_hidden_for_inactive_school_staff(self):
        user = CustomUser.objects.create_user(email='old@ntu.edu.tw', password='pw', name='Old')
        StaffProfile.objects.create(user=user, university='NTU', is_active=False)
        self.assertNotContains(self.page(user), self.BUTTON)

    def test_shown_for_admin_role(self):
        user = CustomUser.objects.create_user(email='admin@readyto.tw', password='pw', name='A', role='admin')
        self.assertContains(self.page(user), self.BUTTON)

    def test_shown_for_superuser(self):
        user = CustomUser.objects.create_superuser(email='root@readyto.tw', password='pw', name='Root')
        self.assertContains(self.page(user), self.BUTTON)

    def test_shown_for_active_school_staff(self):
        user = CustomUser.objects.create_user(email='staff@ntu.edu.tw', password='pw', name='Staff')
        StaffProfile.objects.create(user=user, university='NTU')
        response = self.page(user)
        self.assertContains(response, self.BUTTON)
        self.assertContains(response, reverse('insights:dashboard'))
