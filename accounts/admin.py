from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ["email", "nickname", "gender", "age", "is_staff"]
    ordering = ["email"]
    search_fields = ["email", "nickname"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("개인정보", {"fields": ("nickname", "gender", "age")}),
        ("권한", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nickname", "gender", "age", "password1", "password2"),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")


admin.site.register(User, UserAdmin)