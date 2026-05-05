import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studygo.settings")
django.setup()

from flows.models import FlowStage, Task, Reminder
from users.models import StudentProfile

def fix_all():
    print("1. Triggering auto-translation for FlowStages...")
    for stage in FlowStage.objects.all():
        stage.save()
        print(f"   Translated stage: {stage.name}")
        
    print("\n2. Triggering auto-translation for Tasks...")
    for task in Task.objects.all():
        task.save()
        print(f"   Translated task: {task.title}")

    print("\n3. Fixing Burmese text in StudentProfile.admission_status...")
    profiles = StudentProfile.objects.all()
    for profile in profiles:
        # Check if the admission status is literally Burmese or something weird
        if profile.admission_status == 'ထိုင်ဝမ်မရောက်မီ ပြင်ဆင်ခြင်း':
            profile.admission_status = 'preparing'
            profile.save()
            print(f"   Fixed profile {profile.user.name}")
        elif profile.admission_status == 'arrived' or profile.admission_status == 'pre_arrival':
            pass
        elif profile.admission_status not in ['admitted', 'preparing', 'arrived']:
            # If it's Chinese
            if '準備中' in profile.admission_status:
                profile.admission_status = 'preparing'
                profile.save()
            elif '抵臺' in profile.admission_status:
                profile.admission_status = 'arrived'
                profile.save()
            elif '收到' in profile.admission_status:
                profile.admission_status = 'admitted'
                profile.save()

    print("\nDone.")

if __name__ == "__main__":
    fix_all()
