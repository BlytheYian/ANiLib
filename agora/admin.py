from django.contrib import admin

from .models import Board, Post


class ReplyInline(admin.TabularInline):
    model = Post
    fk_name = 'parent'
    extra = 0
    fields = ('author', 'content', 'created_at')
    readonly_fields = ('created_at',)
    verbose_name = '回覆'
    verbose_name_plural = '樓層回覆'


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'related_anis', 'created_at')
    filter_horizontal = ('anis',)
    search_fields = ('name', 'anis__title')
    ordering = ('name',)

    def related_anis(self, obj):
        titles = list(obj.anis.values_list('title', flat=True))
        return '、'.join(titles[:3]) + ('…' if len(titles) > 3 else '') if titles else '（綜合板）'
    related_anis.short_description = '所屬作品'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'board', 'author', 'reply_count', 'created_at')
    list_filter = ('board',)
    search_fields = ('content', 'author__username')
    ordering = ('-created_at',)
    inlines = [ReplyInline]

    def get_queryset(self, request):
        # 後台只列出主題（樓主貼文），樓層回覆收進主題的 inline 裡
        return super().get_queryset(request).filter(parent__isnull=True)

    def short_content(self, obj):
        return obj.content[:50] + ('…' if len(obj.content) > 50 else '')
    short_content.short_description = '內容'

    def reply_count(self, obj):
        return obj.thread_posts.count()
    reply_count.short_description = '回覆數'
