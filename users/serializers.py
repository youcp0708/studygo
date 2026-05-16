"""
users/serializers.py
DRF Serializers — 負責 request/response 資料驗證與序列化
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import CustomUser, StudentProfile


# ══════════════════════════════════════════
# 1. 註冊 Serializer
# POST /api/users/register/
# ══════════════════════════════════════════
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True,
                                       validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='確認密碼')

    class Meta:
        model  = CustomUser
        fields = ('name', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': '兩次密碼輸入不一致'})
        return attrs

    def validate_email(self, value):
        try:
            existing = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            return value
        if existing.is_active:
            raise serializers.ValidationError('此電子郵件已被註冊')
        raise serializers.ValidationError('此電子郵件已被停用，無法重新註冊')

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(**validated_data)
        return user


# ══════════════════════════════════════════
# 2. 登入 Serializer
# POST /api/users/login/
# ══════════════════════════════════════════
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField(required=True, label='電子郵件')
    password = serializers.CharField(required=True, write_only=True, label='密碼')

    def validate(self, attrs):
        user = authenticate(username=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('電子郵件或密碼錯誤')
        if not user.is_active:
            raise serializers.ValidationError('此帳號已被停用')
        if not user.email_verified:
            raise serializers.ValidationError('請先至信箱完成 Email 驗證後再登入')
        attrs['user'] = user
        return attrs


# ══════════════════════════════════════════
# 3. 學生資料 Serializer
# GET/POST/PATCH /api/users/profile/
# ══════════════════════════════════════════
class StudentProfileSerializer(serializers.ModelSerializer):
    # 顯示 display 文字
    nationality_display      = serializers.CharField(
        source='get_nationality_display',      read_only=True)
    identity_type_display    = serializers.CharField(
        source='get_identity_type_display',    read_only=True)
    admission_status_display = serializers.CharField(
        source='get_admission_status_display', read_only=True)

    class Meta:
        model  = StudentProfile
        fields = (
            'id', 'nationality', 'nationality_display',
            'university', 'department',
            'identity_type', 'identity_type_display',
            'admission_status', 'admission_status_display',
            'expected_arrival', 'preferred_language',
            'has_taiwan_id', 'is_deferred', 'has_indo_prep',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at',
                            'nationality_display', 'identity_type_display',
                            'admission_status_display')
        extra_kwargs = {
            'expected_arrival': {'required': True, 'allow_null': False},
        }

    def validate_nationality(self, value):
        valid = [c[0] for c in StudentProfile.NATIONALITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError('無效的國籍選項')
        return value

    def validate_identity_type(self, value):
        valid = [c[0] for c in StudentProfile.IDENTITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError('無效的身份別選項')
        return value


# ══════════════════════════════════════════
# 4. 使用者完整資料（含 Profile）Serializer
# GET /api/users/me/
# ══════════════════════════════════════════
class UserDetailSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    has_profile     = serializers.SerializerMethodField()

    class Meta:
        model  = CustomUser
        fields = ('id', 'name', 'email', 'role', 'email_verified',
                  'date_joined', 'student_profile', 'has_profile')
        read_only_fields = ('id', 'email', 'role', 'date_joined', 'email_verified')

    def get_has_profile(self, obj):
        return hasattr(obj, 'student_profile') and obj.student_profile is not None


# ══════════════════════════════════════════
# 5. 更新基本資訊 Serializer
# PATCH /api/users/profile/update/
# ══════════════════════════════════════════
class UpdateBasicInfoSerializer(serializers.Serializer):
    name             = serializers.CharField(max_length=100, required=False)
    nationality      = serializers.ChoiceField(
        choices=[c[0] for c in StudentProfile.NATIONALITY_CHOICES], required=False)
    university       = serializers.CharField(max_length=200, required=False)
    department       = serializers.CharField(max_length=200, required=False, allow_blank=True)
    identity_type    = serializers.ChoiceField(
        choices=[c[0] for c in StudentProfile.IDENTITY_CHOICES], required=False)
    admission_status = serializers.ChoiceField(
        choices=[c[0] for c in StudentProfile.ADMISSION_STATUS_CHOICES], required=False)
    expected_arrival = serializers.DateField(required=False, allow_null=True)
    preferred_language = serializers.CharField(max_length=10, required=False)
    has_taiwan_id = serializers.BooleanField(required=False, allow_null=True, default=None)
    is_deferred   = serializers.BooleanField(required=False, allow_null=True, default=None)
    has_indo_prep = serializers.BooleanField(required=False, allow_null=True, default=None)


# ══════════════════════════════════════════
# 6. 修改密碼 Serializer
# POST /api/users/change-password/
# ══════════════════════════════════════════
class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(required=True, write_only=True, label='目前密碼')
    new_password1 = serializers.CharField(required=True, write_only=True,
                                           validators=[validate_password], label='新密碼')
    new_password2 = serializers.CharField(required=True, write_only=True, label='確認新密碼')

    def validate(self, attrs):
        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': '兩次新密碼不一致'})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('目前密碼錯誤')
        return value


# ══════════════════════════════════════════
# 7. 重設密碼申請 Serializer
# POST /api/users/password-reset/
# ══════════════════════════════════════════
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label='電子郵件')

    def validate_email(self, value):
        # 不揭露帳號是否存在（資安考量）
        return value


# ══════════════════════════════════════════
# 8. Token 回應 Serializer（登入後回傳）
# ══════════════════════════════════════════
class AuthResponseSerializer(serializers.Serializer):
    token      = serializers.CharField(read_only=True)
    user       = UserDetailSerializer(read_only=True)
    has_profile = serializers.BooleanField(read_only=True)
