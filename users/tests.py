from django.test import TestCase

from users.models import CustomUser, StudentProfile, AlumniShare
from users.serializers import StudentProfileSerializer, validate_identity_consistency


def base_payload(**overrides):
    data = {
        'region': 'Southeast Asia',
        'nationality': 'Vietnam',
        'university': 'NCU',
        'identity_type': 'foreign_student',
        'admission_status': 'pre_arrival',
        'expected_arrival': '2026-09-01',
    }
    data.update(overrides)
    return data


class IdentityConsistencyTest(TestCase):
    """身份別 / 國籍 / 問答 的一致性驗證（避免任務分流錯誤）"""

    def test_hong_kong_macau_identity_requires_hk_or_macau_nationality(self):
        errors = validate_identity_consistency('hong_kong_macau', 'Vietnam', None)
        self.assertIn('nationality', errors)

    def test_hong_kong_macau_identity_accepts_macau(self):
        errors = validate_identity_consistency('hong_kong_macau', 'Macau', None)
        self.assertEqual(errors, {})

    def test_foreign_student_cannot_be_hk_nationality(self):
        errors = validate_identity_consistency('foreign_student', 'Hong Kong', None)
        self.assertIn('nationality', errors)

    def test_foreign_student_cannot_have_taiwan_id(self):
        errors = validate_identity_consistency('foreign_student', 'Vietnam', True)
        self.assertIn('has_taiwan_id', errors)

    def test_overseas_chinese_any_nationality_ok(self):
        errors = validate_identity_consistency('overseas_chinese', 'Malaysia', True)
        self.assertEqual(errors, {})


class StudentProfileSerializerValidationTest(TestCase):
    def test_valid_payload_passes(self):
        serializer = StudentProfileSerializer(data=base_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_conflicting_identity_and_nationality_rejected(self):
        serializer = StudentProfileSerializer(
            data=base_payload(identity_type='hong_kong_macau', nationality='Vietnam')
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('nationality', serializer.errors)

    def test_foreign_student_with_taiwan_id_rejected(self):
        serializer = StudentProfileSerializer(
            data=base_payload(has_taiwan_id=True)
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('has_taiwan_id', serializer.errors)


def make_user_with_profile(email, university='NCU', nationality='Vietnam'):
    user = CustomUser.objects.create_user(email=email, password='pw', name=email.split('@')[0])
    StudentProfile.objects.create(
        user=user,
        nationality=nationality,
        university=university,
        identity_type='foreign_student',
        admission_status='pre_arrival',
    )
    return user


class AlumniSharePageTest(TestCase):
    """學長姐分享區：左側分頁導覽（我的分享 / 我的學校 / 所有學校）+ 篩選與搜尋"""

    def setUp(self):
        self.ncu_user = make_user_with_profile('ncu@test.com', university='NCU')
        profile = self.ncu_user.student_profile
        profile.department = '資訊管理學系'
        profile.save()
        self.ntu_user = make_user_with_profile('ntu@test.com', university='NTU', nationality='Japan')

    def test_post_creates_share_with_school_and_dept_snapshot(self):
        self.client.force_login(self.ncu_user)
        response = self.client.post('/alumni/', {
            'title': '宿舍申請注意事項',
            'content': '中央大學宿舍申請要早點排隊！',
        })
        self.assertEqual(response.status_code, 302)  # PRG redirect

        share = AlumniShare.objects.get()
        self.assertEqual(share.title, '宿舍申請注意事項')
        self.assertEqual(share.university, 'NCU')            # 自動快照學校
        self.assertEqual(share.nationality, 'Vietnam')       # 自動快照國籍
        self.assertEqual(share.program, '資訊管理學系')      # 系所由個人資料自動快照

    def test_mine_tab_shows_only_my_posts(self):
        AlumniShare.objects.create(user=self.ncu_user, university='NCU', content='我的內容')
        AlumniShare.objects.create(user=self.ntu_user, university='NTU', content='別人的內容')
        self.client.force_login(self.ncu_user)
        response = self.client.get('/alumni/?tab=mine')
        self.assertEqual(len(response.context['shares']), 1)
        self.assertContains(response, '我的內容')
        self.assertNotContains(response, '別人的內容')

    def test_school_tab_defaults_to_all_departments(self):
        # 同校兩篇：一篇同系、一篇不同系 → 預設兩篇都顯示（系所預設為「全部系所」）
        AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', program='資訊管理學系', content='資管的分享')
        AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', program='機械工程學系', content='機械的分享')
        self.client.force_login(self.ncu_user)

        response = self.client.get('/alumni/?tab=school')
        self.assertEqual(response.context['selected_dept'], '')
        self.assertContains(response, '資管的分享')
        self.assertContains(response, '機械的分享')

        # 明確選特定系所 → 只顯示該系所
        response = self.client.get('/alumni/?tab=school&dept=資訊管理學系')
        self.assertContains(response, '資管的分享')
        self.assertNotContains(response, '機械的分享')

    def test_school_tab_excludes_other_schools(self):
        AlumniShare.objects.create(user=self.ntu_user, university='NTU', content='NTU 的心得')
        self.client.force_login(self.ncu_user)
        response = self.client.get('/alumni/?tab=school&dept=')
        self.assertNotContains(response, 'NTU 的心得')

    def test_all_tab_school_filter(self):
        AlumniShare.objects.create(user=self.ncu_user, university='NCU', content='NCU 的心得')
        AlumniShare.objects.create(user=self.ntu_user, university='NTU', content='NTU 的心得')
        self.client.force_login(self.ncu_user)

        # 未指定學校 → 預設帶入使用者自己的學校（NCU）
        response = self.client.get('/alumni/?tab=all')
        self.assertEqual(response.context['selected_school'], 'NCU')
        self.assertContains(response, 'NCU 的心得')
        self.assertNotContains(response, 'NTU 的心得')

        response = self.client.get('/alumni/?tab=all&school=NTU')
        self.assertContains(response, 'NTU 的心得')
        self.assertNotContains(response, 'NCU 的心得')

        # 明確選「全部學校」（school 為空）→ 兩篇都顯示
        response = self.client.get('/alumni/?tab=all&school=')
        self.assertEqual(len(response.context['shares']), 2)

    def test_text_search(self):
        AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', title='宿舍攻略', content='床墊要自己買')
        AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', title='選課心得', content='加退選拼手速')
        self.client.force_login(self.ncu_user)

        response = self.client.get('/alumni/?tab=all&q=宿舍')
        self.assertContains(response, '宿舍攻略')
        self.assertNotContains(response, '選課心得')

    def test_inactive_share_hidden(self):
        AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', content='被下架的內容', is_active=False,
        )
        self.client.force_login(self.ncu_user)
        response = self.client.get('/alumni/?tab=all')
        self.assertNotContains(response, '被下架的內容')

    def test_empty_content_not_created(self):
        self.client.force_login(self.ncu_user)
        self.client.post('/alumni/', {'title': 'x', 'content': '   '})
        self.assertEqual(AlumniShare.objects.count(), 0)

    def test_requires_login(self):
        response = self.client.get('/alumni/')
        self.assertEqual(response.status_code, 302)

    def test_user_can_delete_own_share(self):
        share = AlumniShare.objects.create(
            user=self.ncu_user, university='NCU', content='要刪掉的內容')
        self.client.force_login(self.ncu_user)
        resp = self.client.post('/alumni/delete/', {'share_id': share.id})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(AlumniShare.objects.filter(id=share.id).exists())

    def test_user_cannot_delete_others_share(self):
        share = AlumniShare.objects.create(
            user=self.ntu_user, university='NTU', content='別人的內容')
        self.client.force_login(self.ncu_user)
        self.client.post('/alumni/delete/', {'share_id': share.id})
        # 非本人 → 不應被刪除
        self.assertTrue(AlumniShare.objects.filter(id=share.id).exists())

    def test_mine_tab_shows_delete_button(self):
        AlumniShare.objects.create(user=self.ncu_user, university='NCU', content='我的分享')
        self.client.force_login(self.ncu_user)
        resp = self.client.get('/alumni/?tab=mine')
        self.assertContains(resp, 'alumni/delete/')

    def test_school_tab_has_no_delete_button(self):
        AlumniShare.objects.create(user=self.ncu_user, university='NCU', content='我的分享')
        self.client.force_login(self.ncu_user)
        resp = self.client.get('/alumni/?tab=school&dept=')
        self.assertNotContains(resp, 'alumni/delete/')
