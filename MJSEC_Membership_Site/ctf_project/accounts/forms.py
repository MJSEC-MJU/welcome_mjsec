from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Profile

# Validator 정의
username_validator = RegexValidator(
    regex=r'^[A-Za-z0-9]{5,}$',
    message='아이디는 영문 대소문자·숫자만 사용하여 최소 5자 이상이어야 합니다.'
)
student_id_validator = RegexValidator(
    regex=r'^[0-9]+$',
    message='학번은 숫자만 입력해야 합니다.'
)
password_validator = RegexValidator(
    regex=r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,}',
    message='비밀번호는 최소 8자, 대문자·소문자·숫자·특수문자 각각 1개 이상 포함해야 합니다.'
)

class SignUpForm(UserCreationForm):
    username   = forms.CharField(
        label="아이디",
        max_length=150,
        validators=[username_validator],
        help_text="영문·숫자만, 최소 5자 이상"
    )
    name       = forms.CharField(label="이름", max_length=30)
    student_id = forms.CharField(
        label="학번",
        max_length=20,
        validators=[student_id_validator],
        help_text="숫자만 입력"
    )
    department = forms.CharField(label="학과", max_length=50)
    password1  = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput,
        validators=[password_validator],
        help_text="최소 8자, 대문자·소문자·숫자·특수문자 포함"
    )
    password2  = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("username", "name", "student_id", "department", "password1", "password2")

    def clean_password2(self):
        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        # User 모델의 first_name에 이름 저장
        user.first_name = self.cleaned_data["name"]
        if commit:
            user.save()
            # Profile에 학번·학과 저장
            Profile.objects.filter(user=user).update(
                student_id=self.cleaned_data["student_id"],
                department=self.cleaned_data["department"]
            )
        return user
