from django.test import TestCase
from users.models import CustomUser, StudentProfile
from flows.models import FlowStage, Task, StudentTask, Reminder


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
