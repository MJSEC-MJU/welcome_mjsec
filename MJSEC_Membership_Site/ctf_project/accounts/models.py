from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id  = models.CharField("학번", max_length=20)
    department  = models.CharField("학과", max_length=50)

    def __str__(self):
        return f"{self.user.username} 프로필"
