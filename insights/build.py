"""
insights/build.py
ETL：從營運資料表產生去識別化的分析表（規格 §8）。

每次執行都整批重建「非模擬」資料（is_demo=False），模擬資料不受影響。
只讀取 users / flows / chatbot 的資料表，不修改它們。
"""

import hashlib
import hmac
from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from chatbot.services import compute_task_due_date
from flows.models import Reminder, StudentTask
from users.models import StudentProfile

from . import conf
from .alerts import rebuild_alerts
from .metrics import academic_year_of, arrival_cohort_of
from .models import (
    DimStudent, FactQuestion, FactStudentTask, QuestionClassification,
    StaffAccess, StaffProfile,
)
from .task_categories import classify_task

BATCH_SIZE = 1000

# 到期「前」的提醒才算數；overdue 提醒是逾期之後才發的，算進去會倒因為果
PRE_DUE_REMINDER_KINDS = ('due_soon', 'due_today')


def student_key(profile_id):
    """HMAC-SHA256 雜湊後的學生代碼。沒有密鑰無法反推回 StudentProfile.id。"""
    digest = hmac.new(conf.hash_key(), str(profile_id).encode('utf-8'), hashlib.sha256)
    return digest.hexdigest()[:32]


def analyzable_students():
    """
    納入統計的學生：排除停用帳號、管理員、校方人員、測試帳號。
    """
    qs = StudentProfile.objects.filter(
        user__is_active=True,
        user__role='student',
        user__is_staff=False,
        user__is_superuser=False,
    ).exclude(user__insights_staff_profile__isnull=False)

    excluded = Q()
    for domain in conf.excluded_email_domains():
        excluded |= Q(user__email__iendswith='@' + domain)
    emails = conf.excluded_emails()
    if emails:
        excluded |= Q(user__email__in=emails)
    if excluded:
        qs = qs.exclude(excluded)
    return qs.select_related('user')


def _dimensions(profile):
    return {
        'student_key': student_key(profile.id),
        'university': profile.university,
        'nationality': profile.nationality,
        'region': profile.region or '',
        'identity_type': profile.identity_type,
        'arrival_cohort': arrival_cohort_of(profile.expected_arrival),
        'academic_year': academic_year_of(profile.expected_arrival),
    }


def _fact_for(st, profile, dims, snapshot_date, reminder_counts, inactive_since):
    task = st.task
    due = compute_task_due_date(task, profile)
    has_deadline = due is not None
    is_completed = st.status == 'completed'
    completed_date = timezone.localtime(st.completed_at).date() if st.completed_at else None

    # 已到期：截止日已過（截止日 < 資料日期）
    is_due = has_deadline and due < snapshot_date
    is_overdue_open = is_due and not is_completed
    is_overdue_late = bool(is_completed and has_deadline and completed_date and completed_date > due)
    last_login = profile.user.last_login
    is_possibly_unreported = is_overdue_open and (last_login is None or last_login < inactive_since)

    return FactStudentTask(
        snapshot_date=snapshot_date,
        task_category=classify_task(task),
        is_required=task.is_required,
        has_deadline=has_deadline,
        due_date=due,
        status=st.status,
        completed_date=completed_date,
        is_completed=is_completed,
        is_due=is_due,
        is_overdue_open=is_overdue_open,
        is_overdue_late=is_overdue_late,
        is_overdue=is_overdue_open or is_overdue_late,
        is_possibly_unreported=is_possibly_unreported,
        reminder_count=min(reminder_counts.get(st.id, 0), 32767),
        **dims,
    )


@transaction.atomic
def build_snapshot(snapshot_date=None):
    """
    重建所有非模擬分析表。回傳摘要 dict（供 management command 顯示）。
    """
    snapshot_date = snapshot_date or timezone.localdate()
    inactive_since = timezone.now() - timedelta(days=conf.UNREPORTED_INACTIVE_DAYS)

    for model in (DimStudent, FactStudentTask, FactQuestion, StaffAccess):
        model.objects.filter(is_demo=False).delete()

    # ── 學生 ──
    profiles = {p.id: p for p in analyzable_students()}
    dims_by_id = {pid: _dimensions(p) for pid, p in profiles.items()}
    DimStudent.objects.bulk_create(
        [
            DimStudent(
                snapshot_date=snapshot_date,
                admission_status=p.admission_status,
                preferred_language=p.preferred_language or '',
                **dims_by_id[pid],
            )
            for pid, p in profiles.items()
        ],
        batch_size=BATCH_SIZE,
    )

    # ── 學生任務 ──
    reminder_counts = Counter(
        Reminder.objects.filter(kind__in=PRE_DUE_REMINDER_KINDS, student_task__isnull=False)
        .values_list('student_task_id', flat=True)
    )
    student_tasks = (
        StudentTask.objects.filter(student_id__in=profiles.keys())
        .select_related('task')
        .iterator(chunk_size=BATCH_SIZE)
    )
    facts, unmapped = [], Counter()
    for st in student_tasks:
        profile = profiles[st.student_id]
        fact = _fact_for(st, profile, dims_by_id[st.student_id], snapshot_date, reminder_counts, inactive_since)
        if fact.task_category == 'other':
            unmapped[(st.task_id, st.task.task_code, st.task.title)] += 1
        facts.append(fact)
        if len(facts) >= BATCH_SIZE:
            FactStudentTask.objects.bulk_create(facts)
            facts = []
    FactStudentTask.objects.bulk_create(facts)

    # ── 學生提問（只取 helper 模式；分類結果來自 classify_questions）──
    classifications = (
        QuestionClassification.objects.filter(
            message__role='user',
            message__session__ai_mode='helper',
            message__session__user__student_profile__id__in=profiles.keys(),
        )
        .values_list('category', 'message__created_at', 'message__session__user__student_profile__id')
        .iterator(chunk_size=BATCH_SIZE)
    )
    questions = [
        FactQuestion(
            snapshot_date=snapshot_date,
            category=category,
            asked_date=timezone.localtime(created_at).date(),
            **dims_by_id[pid],
        )
        for category, created_at, pid in classifications
    ]
    FactQuestion.objects.bulk_create(questions, batch_size=BATCH_SIZE)

    # ── Power BI RLS 對照表 ──
    StaffAccess.objects.bulk_create([
        StaffAccess(snapshot_date=snapshot_date, powerbi_upn=sp.powerbi_upn.lower(), university=sp.university)
        for sp in StaffProfile.objects.filter(is_active=True).exclude(powerbi_upn='')
    ])

    alert_count = rebuild_alerts(snapshot_date, is_demo=False)

    return {
        'snapshot_date': snapshot_date,
        'students': len(profiles),
        'student_tasks': FactStudentTask.objects.filter(is_demo=False).count(),
        'questions': len(questions),
        'alerts': alert_count,
        'unmapped_tasks': [
            {'task_id': tid, 'task_code': code, 'title': title, 'rows': n}
            for (tid, code, title), n in unmapped.most_common()
        ],
    }
