from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # 관리자 페이지에 프로필 정보를 표시할 컬럼 설정
    list_display = (
        'user',          # 사용자
        'student_id',    # 학번
        'department'     # 학과
    )
    # 관리자 페이지 검색 기능에 사용할 필드 설정
    search_fields = (
        'user__username',
        'student_id',
        'department'
    )
