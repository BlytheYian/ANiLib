from django.contrib import admin
from django import forms
from django.db import models
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.core.files.base import ContentFile
import os
from io import BytesIO
from PIL import Image
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter

from .models import Ani, Tag, Creator, Studio, Episode, AniAlias, SyncJob, UserReview

class NoAutocompleteModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'

class AliasInline(admin.TabularInline):
    model = AniAlias
    extra = 1
    verbose_name = "別名"
    verbose_name_plural = "別名列表"
    form = NoAutocompleteModelForm

class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1
    verbose_name = "更新集數"
    verbose_name_plural = "集數列表"
    form = NoAutocompleteModelForm

class AniInline(admin.TabularInline):
    model = Ani.creators.through
    extra = 1
    verbose_name = "參與的動畫"
    verbose_name_plural = "參與的動畫列表"

@admin.register(Ani)
class AniAdmin(admin.ModelAdmin):
    form = NoAutocompleteModelForm
    change_list_template = 'admin/ani/ani/change_list.html'
    change_form_template  = 'admin/ani/ani/change_form.html'

    def get_urls(self):
        custom = [
            path('imdb_sync_start/',
                 self.admin_site.admin_view(self._sync_start),
                 name='ani_ani_imdb_sync_start'),
            path('imdb_sync_single/<int:pk>/',
                 self.admin_site.admin_view(self._sync_single),
                 name='ani_ani_imdb_sync_single'),
            path('imdb_sync_status/<int:job_id>/',
                 self.admin_site.admin_view(self._sync_status),
                 name='ani_ani_imdb_sync_status'),
        ]
        return custom + super().get_urls()

    def _sync_start(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        from django.conf import settings
        from .imdb_sync import parse_watchlist_csv, start_sync
        import re as _re

        csv_file  = request.FILES.get('csv_file')
        ids_text  = request.POST.get('ids', '').strip()
        use_wl    = request.POST.get('use_watchlist') == '1'

        if csv_file:
            try:
                text = csv_file.read().decode('utf-8-sig')
            except Exception:
                return JsonResponse({'error': 'CSV 讀取失敗'}, status=400)
            ids = parse_watchlist_csv(text)
        elif ids_text:
            ids = list(dict.fromkeys(
                m.group(0) for m in _re.finditer(r'tt\d{7,}', ids_text)
            ))
        elif use_wl:
            url = getattr(settings, 'IMDB_WATCHLIST_URL', None)
            if not url:
                return JsonResponse({'error': '請在 settings.py 設定 IMDB_WATCHLIST_URL'}, status=400)
            # IDs will be fetched inside the browser session in the job worker
            ids = [f'__watchlist__{url}']  # sentinel handled in _run_job
        else:
            return JsonResponse({'error': '請上傳 CSV、貼上 ID 或選擇使用 Watchlist'}, status=400)

        if not ids:
            return JsonResponse({'error': '未找到任何有效的 IMDb ID'}, status=400)
        force_stars = request.POST.get('force_stars') == '1'
        new_only    = request.POST.get('new_only')    == '1'
        smart_scan  = request.POST.get('smart_scan')  == '1'
        job_id = start_sync(ids, force_stars=force_stars,
                            new_only=new_only, smart_scan=smart_scan)
        return JsonResponse({'job_id': job_id, 'total': len(ids)})

    def _sync_single(self, request, pk):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST only'}, status=405)
        from .imdb_sync import start_sync
        from django.shortcuts import get_object_or_404
        ani = get_object_or_404(Ani, pk=pk)
        if not ani.IMDb_ID:
            return JsonResponse({'error': '此動畫尚未設定 IMDb ID'}, status=400)
        job_id = start_sync([ani.IMDb_ID])
        return JsonResponse({'job_id': job_id, 'total': 1})

    def _sync_status(self, request, job_id):
        try:
            job = SyncJob.objects.get(id=job_id)
            pct = int(job.progress / job.total * 100) if job.total else 0
            return JsonResponse({
                'status':   job.status,
                'progress': job.progress,
                'total':    job.total,
                'pct':      pct,
                'log':      job.log,
            })
        except SyncJob.DoesNotExist:
            return JsonResponse({'error': 'not found'}, status=404)
    
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status')
    list_editable = ('status',)
    ordering = ('title',) 
    search_fields = ('title', 'title_zh', 'title_ch', 'IMDb_ID', 'aliases__title')
    
    list_filter = (
        ('year', DropdownFilter),
        ('status', ChoiceDropdownFilter),
        ('tags', RelatedDropdownFilter),
    )
    
    filter_horizontal = ('creators', 'tags', 'studio')
    
    def poster_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" style="width: 150px; height: auto; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);" />', obj.poster.url)
        return "尚未上傳海報"

    def banner_preview(self, obj):
        if obj.banner:
            return format_html('<img src="{}" style="width: 300px; height: auto; border-radius: 5px;" />', obj.banner.url)
        return "尚未上傳橫幅"

    poster_preview.short_description = "海報預覽"
    banner_preview.short_description = "橫幅預覽"

    readonly_fields = ['poster_preview', 'banner_preview']# 唯讀
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', ('title_ch', 'title_zh'), 'description')
        }),
        ('視覺素材', {
            'fields': (
                'poster', 'poster_preview',
                'banner', 'banner_preview'
            ),
            'classes': ('collapse',),
        }),
        ('播放數據', {
            'fields': (('year', 'runtime'), ('total_seasons', 'total_episodes'))
        }),
        ('外部連結與評分', {
            'fields': ('IMDb_ID', 'imdb_stars', 'status', 'rating'),
        }),
        ('關聯分類', {
            'fields': ('studio', 'creators', 'tags'),
        }),
    )
    
    inlines = [AliasInline, EpisodeInline]

@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_animations')
    inlines = [AniInline]
    ordering = ('name',) 
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('ani_set')
        
    def display_animations(self, obj):
        return ", ".join([ani.title for ani in obj.ani_set.all()])
    
    display_animations.short_description = '參與作品'

admin.site.register(Tag)
admin.site.register(Studio)
admin.site.register(Episode)


@admin.register(UserReview)
class UserReviewAdmin(admin.ModelAdmin):
    list_display  = ('user', 'ani', 'score', 'short_text', 'updated_at')
    list_filter   = ('score',)
    search_fields = ('user__username', 'ani__title', 'text')
    ordering      = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at', 'text')

    def short_text(self, obj):
        return obj.text[:50] + ('…' if len(obj.text) > 50 else '')
    short_text.short_description = '評論內容'


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display  = ['id', 'status', 'progress', 'total', 'created_at', 'finished_at']
    readonly_fields = ['status', 'progress', 'total', 'log', 'created_at', 'finished_at']

    def has_add_permission(self, request):
        return False