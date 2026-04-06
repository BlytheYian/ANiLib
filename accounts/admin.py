from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    readonly_fields = ('following_anis',)
    fieldsets = UserAdmin.fieldsets + (
        ('自訂資訊',{
            'fields': ('avatar', 'following_anis'),
        }),
    )
    def get_following_count(self, obj):
        return obj.following_anis.count()
    get_following_count.short_description = "追番數量"
    list_display = ('username', 'email', 'is_staff', 'get_following_count')
#admin.site.register(CustomUser, UserAdmin)