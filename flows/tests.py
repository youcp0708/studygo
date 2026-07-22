from django.test import TestCase
from rest_framework.test import APIClient
from users.models import CustomUser, StudentProfile
from flows.models import FlowStage, Task, StudentTask, Reminder
from datetime import date



def make_student(email="test@test.com"):
    user = CustomUser.objects.create_user(email=email, password="pw", name="Test")
    return StudentProfile.objects.create(
        user=user,
        nationality="Japan",
        university="NTU",
        identity_type="foreign_student",
        admission_status="pre_arrival",
    )


class FlowStageGetNameByLangTest(TestCase):
    def setUp(self):
        self.stage = FlowStage.objects.create(name="申請來台", name_en="Apply to Taiwan", order=1)

    def test_returns_translation_when_available(self):
        self.assertEqual(self.stage.get_name_by_lang("en"), "Apply to Taiwan")

    def test_falls_back_to_chinese_when_translation_empty(self):
        self.assertEqual(self.stage.get_name_by_lang("my"), "申請來台")

    def test_falls_back_to_chinese_for_unknown_lang(self):
        self.assertEqual(self.stage.get_name_by_lang("xx"), "申請來台")


class TaskGetLocalizedTest(TestCase):
    def setUp(self):
        stage = FlowStage.objects.create(name="Stage", order=1)
        self.task = Task.objects.create(
            stage=stage,
            title="辦理簽證",
            title_en="Apply for Visa",
            description="說明",
            description_en="Description",
            order=1,
        )

    def test_returns_translated_fields(self):
        result = self.task.get_localized("en")
        self.assertEqual(result["title"], "Apply for Visa")
        self.assertEqual(result["description"], "Description")

    def test_falls_back_to_chinese_when_translation_empty(self):
        result = self.task.get_localized("my")
        self.assertEqual(result["title"], "辦理簽證")

    def test_returns_chinese_for_unsupported_lang(self):
        result = self.task.get_localized("zh")
        self.assertEqual(result["title"], "辦理簽證")


class ReminderSignalTest(TestCase):
    def setUp(self):
        self.student = make_student()
        stage = FlowStage.objects.create(name="Stage", order=1)
        self.task1 = Task.objects.create(stage=stage, title="Task 1", order=1)
        self.task2 = Task.objects.create(stage=stage, title="Task 2", order=2)
        self.st1 = StudentTask.objects.create(student=self.student, task=self.task1, status="not_started")
        self.st2 = StudentTask.objects.create(student=self.student, task=self.task2, status="not_started")

    def test_reminder_created_when_task_completed_out_of_order(self):
        self.st2.status = "completed"
        self.st2.save()
        self.assertEqual(Reminder.objects.filter(student=self.student).count(), 1)

    def test_no_reminder_when_tasks_completed_in_order(self):
        self.st1.status = "completed"
        self.st1.save()
        self.st2.status = "completed"
        self.st2.save()
        self.assertEqual(Reminder.objects.filter(student=self.student).count(), 0)

    def test_no_duplicate_reminder_on_repeated_save(self):
        self.st2.status = "completed"
        self.st2.save()
        self.st2.save()  # signal fires again, but duplicate should be suppressed
        self.assertEqual(Reminder.objects.filter(student=self.student).count(), 1)


class CheckRemindersCommandTest(TestCase):
    def setUp(self):
        self.student = make_student(email="test_reminder@example.com")
        self.stage = FlowStage.objects.create(name="Stage 1", order=1)
        self.task = Task.objects.create(
            stage=self.stage,
            title="Task with Deadline",
            deadline_type="absolute",
            deadline_date=date(2026, 6, 28),
            order=1
        )
        self.st = StudentTask.objects.create(
            student=self.student,
            task=self.task,
            status="not_started"
        )

    def test_command_creates_reminder_and_handles_deadline_change(self):
        from django.core.management import call_command
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()

        # Set deadline to today + 2 days (within 3 days warning window)
        self.task.deadline_date = today + timedelta(days=2)
        self.task.save()

        # 1. Run check_reminders command. Since --days defaults to 3, it should trigger.
        call_command('check_reminders')

        # Verify 1 reminder is created
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 1)
        reminder = Reminder.objects.get(student_task=self.st)
        self.assertFalse(reminder.is_read)
        self.assertIn(str(self.task.deadline_date), reminder.message)

        # 2. Running it again should NOT create a duplicate reminder
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 1)

        # 3. Even if the reminder is marked as read, running it again with the same deadline should NOT duplicate
        reminder.is_read = True
        reminder.save()
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 1)

        # 4. Now, change the deadline to today + 1 day (deadline changed!)
        self.task.deadline_date = today + timedelta(days=1)
        self.task.save()

        # Run command again. It should create a NEW reminder for the new deadline
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 2)

        # The new reminder should be unread, and contain the new deadline date
        new_reminder = Reminder.objects.filter(student_task=self.st, is_read=False).first()
        self.assertIsNotNone(new_reminder)
        self.assertIn(str(self.task.deadline_date), new_reminder.message)

    def test_command_keeps_undated_prerequisite_reminders(self):
        """訊號產生的前置任務提醒（訊息不含日期）不應被到期提醒的清理邏輯誤刪"""
        from django.core.management import call_command
        prerequisite_reminder = Reminder.objects.create(
            student=self.student,
            student_task=self.st,
            message='您已完成「Task B」，但前置任務「Task A」尚未完成，建議您依序完成！',
        )
        from django.utils import timezone
        from datetime import timedelta
        self.task.deadline_date = timezone.now().date() + timedelta(days=2)
        self.task.save()

        call_command('check_reminders')

        self.assertTrue(
            Reminder.objects.filter(id=prerequisite_reminder.id).exists(),
            '不含日期的前置任務提醒被誤刪了'
        )

    def test_command_cleans_up_old_unread_reminders_on_deadline_change(self):
        from django.core.management import call_command
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()

        self.task.deadline_date = today + timedelta(days=2)
        self.task.save()

        # Run command to create the initial reminder
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st, is_read=False).count(), 1)

        # Change the deadline to a future date outside the window (e.g. today + 10 days)
        self.task.deadline_date = today + timedelta(days=10)
        self.task.save()

        # Run command again. The old unread reminder should be deleted, and no new reminder should be created
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 0)


class ReminderApiLazySyncTest(TestCase):
    """鈴鐺 API 應該在使用者打開通知時即時補上過期提醒，不必等 check_reminders 排程先跑過"""

    def setUp(self):
        self.student = make_student(email="lazy_sync@example.com")
        self.stage = FlowStage.objects.create(name="Stage 1", order=1)
        self.task = Task.objects.create(
            stage=self.stage,
            title="Overdue Task",
            deadline_type="absolute",
            deadline_date=date(2026, 6, 28),  # already in the past
            order=1
        )
        self.st = StudentTask.objects.create(
            student=self.student,
            task=self.task,
            status="not_started"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.student.user)

    def test_overdue_reminder_appears_without_running_command_first(self):
        # No check_reminders call here on purpose — the API itself should generate it.
        response = self.client.get('/api/flows/reminders/')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 1)
        reminder = Reminder.objects.get(student_task=self.st)
        self.assertIn('已過期', reminder.message)

        data = response.json()['data']
        self.assertEqual(data['unread_count'], 1)
        self.assertTrue(any('已過期' in r['message'] for r in data['reminders']))

    def test_lazy_sync_does_not_send_email(self):
        from django.core import mail
        self.client.get('/api/flows/reminders/')
        self.assertEqual(len(mail.outbox), 0)

    def test_command_creates_overdue_reminder_even_if_upcoming_reminder_exists(self):
        from django.core.management import call_command
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()

        # 1. Create upcoming reminder when deadline is today + 2 days
        self.task.deadline_date = today + timedelta(days=2)
        self.task.save()
        call_command('check_reminders')
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 1)
        upcoming_reminder = Reminder.objects.get(student_task=self.st)
        self.assertIn("天後到期", upcoming_reminder.message)

        # Mark as read (to simulate user reading it)
        upcoming_reminder.is_read = True
        upcoming_reminder.save()

        # 2. Suppose time passes, and the deadline is now in the past (deadline is today - 1 day)
        self.task.deadline_date = today - timedelta(days=1)
        self.task.save()

        # Run command again. An overdue reminder should be created
        call_command('check_reminders')
        
        # Now there should be 2 reminders (1 upcoming, 1 overdue)
        self.assertEqual(Reminder.objects.filter(student_task=self.st).count(), 2)
        overdue_reminder = Reminder.objects.filter(student_task=self.st, is_read=False).first()
        self.assertIsNotNone(overdue_reminder)
        self.assertIn("已過期", overdue_reminder.message)




class InitStudentTasksSyncTest(TestCase):
    """任務同步（init API）：去重 key、進度保留、is_pre_arrival 自動完成"""

    def setUp(self):
        self.student = make_student(email="sync@test.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.student.user)
        self.stage1 = FlowStage.objects.create(name="入台前", order=1, is_pre_arrival=True)
        self.stage2 = FlowStage.objects.create(name="抵台後", order=2)

    def init(self):
        return self.client.post('/api/flows/my-tasks/init/')

    def test_same_title_in_different_stages_not_deduped(self):
        Task.objects.create(stage=self.stage1, title="繳交文件", order=1)
        Task.objects.create(stage=self.stage2, title="繳交文件", order=1)
        self.init()
        self.assertEqual(StudentTask.objects.filter(student=self.student).count(), 2)

    def test_task_code_dedup_keeps_most_specific(self):
        generic = Task.objects.create(stage=self.stage1, title="辦簽證(通用)", task_code="apply_visa", order=1)
        specific = Task.objects.create(
            stage=self.stage1, title="辦簽證(日本)", task_code="APPLY_VISA",  # 大小寫不同也應視為同一類
            nationality=['Japan'], order=2,
        )
        self.init()
        tasks = StudentTask.objects.filter(student=self.student)
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().task_id, specific.id)

    def test_in_progress_task_not_removed_when_no_longer_eligible(self):
        task = Task.objects.create(stage=self.stage1, title="舊任務", order=1)
        self.init()
        st = StudentTask.objects.get(student=self.student, task=task)
        st.status = 'in_progress'
        st.note = '已經跑了一半'
        st.save()

        # admin 把任務改成只給僑生（此學生是外籍生）→ 不再符合條件
        task.identity_type = ['overseas_chinese']
        task.save()
        self.init()

        self.assertTrue(
            StudentTask.objects.filter(id=st.id).exists(),
            '進行中的任務（含備註）不應在條件變更時被刪除'
        )

    def test_not_started_task_removed_when_no_longer_eligible(self):
        task = Task.objects.create(stage=self.stage1, title="舊任務", order=1)
        self.init()
        task.identity_type = ['overseas_chinese']
        task.save()
        self.init()
        self.assertFalse(StudentTask.objects.filter(student=self.student, task=task).exists())

    def test_arrived_student_auto_completes_pre_arrival_stage(self):
        Task.objects.create(stage=self.stage1, title="入台前任務", order=1)
        Task.objects.create(stage=self.stage2, title="抵台後任務", order=1)
        self.student.admission_status = 'arrived'
        self.student.save()
        self.init()

        pre = StudentTask.objects.get(student=self.student, task__stage=self.stage1)
        post = StudentTask.objects.get(student=self.student, task__stage=self.stage2)
        self.assertEqual(pre.status, 'completed')
        self.assertEqual(post.status, 'not_started')
