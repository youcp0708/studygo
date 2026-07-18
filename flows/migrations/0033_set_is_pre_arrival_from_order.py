# 資料遷移：沿用舊行為（order=1 的階段視為「入臺前」），
# 將既有資料的 is_pre_arrival 補上，之後即可在 Admin 自由調整。

from django.db import migrations


def set_pre_arrival(apps, schema_editor):
    FlowStage = apps.get_model('flows', 'FlowStage')
    FlowStage.objects.filter(order=1).update(is_pre_arrival=True)


def unset_pre_arrival(apps, schema_editor):
    FlowStage = apps.get_model('flows', 'FlowStage')
    FlowStage.objects.filter(order=1).update(is_pre_arrival=False)


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0032_flowstage_is_pre_arrival'),
    ]

    operations = [
        migrations.RunPython(set_pre_arrival, unset_pre_arrival),
    ]
