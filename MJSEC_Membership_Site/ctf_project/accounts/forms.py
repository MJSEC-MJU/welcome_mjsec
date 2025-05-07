from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class SignUpForm(UserCreationForm):
    name       = forms.CharField(label="이름", max_length=30)
    student_id = forms.CharField(label="학번", max_length=20)
    department = forms.CharField(label="학과", max_length=50)

    class Meta:
        model = User
        fields = ("username", "name", "student_id", "department", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        # User 모델의 first_name에 이름 저장
        user.first_name = self.cleaned_data['name']
        if commit:
            user.save()
            # Profile에 학번·학과 저장
            Profile.objects.filter(user=user).update(
                student_id=self.cleaned_data['student_id'],
                department=self.cleaned_data['department']
            )
        return user
