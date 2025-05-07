from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # 관리자 페이지에 프로필 정보를 표시할 컬럼 설정
    list_display = (
        'user',          # 사용자 계정 (아이디)
        'name',          # 이름
        'student_id',    # 학번
        'department'     # 학과
    )
    # 관리자 페이지 검색 기능에 사용할 필드 설정
    search_fields = (
        'user__username',
        'user__first_name',  # 이름 검색
        'user__last_name',   # 성 검색
        'student_id',
        'department'
    )

    
    @admin.display(description='이름')
    def name(self, obj):
        full_name = obj.user.get_full_name()
        return full_name if full_name else '-'