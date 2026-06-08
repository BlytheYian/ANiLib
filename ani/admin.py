from django.contrib import admin
from django import forms
from django.db import models
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from django.core.files.base import ContentFile
import os
from io import BytesIO
from PIL import Image
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter

from .models import Ani, Tag, Person, Studio, Episode, AniAlias, SyncJob, UserReview, Character, Series

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

class CharacterInline(admin.StackedInline):
    model = Character
    extra = 0
    verbose_name = "角色"
    verbose_name_plural = "角色列表"
    form = NoAutocompleteModelForm
    show_change_link = True
    readonly_fields = ('image_focus_editor',)
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 3, 'autocomplete': 'off'})},
    }

    fieldsets = (
        (None, {
            'fields': (
                ('order', 'name', 'name_zh'),
                'va',
                'description',
                ('image', 'image_focus_editor'),
                ('image_focus_x', 'image_focus_y', 'image_scale'),
            )
        }),
    )

    class Media:
        js  = ('admin/js/char_image_editor.js',)
        css = {'all': ('admin/css/char_image_editor.css',)}

    def image_focus_editor(self, obj):
        if not obj.pk or not obj.image:
            return mark_safe(
                '<p class="help" style="color:#888;font-style:italic;">'
                '儲存圖片後即可調整焦點與縮放</p>'
            )
        return format_html(
            '<div class="char-focus-editor" data-x="{x}" data-y="{y}" data-scale="{s}">'
            '  <div class="focus-preview-wrap">'
            '    <img src="{src}" alt="">'
            '    <div class="focus-dot"></div>'
            '    <div class="focus-hint">點擊設定焦點・滾輪縮放</div>'
            '  </div>'
            '  <div class="focus-zoom-row">'
            '    <label>縮放</label>'
            '    <input type="range" class="focus-scale-slider"'
            '           min="0.5" max="4" step="0.05" value="{s}">'
            '    <span class="focus-scale-val">{sf}×</span>'
            '  </div>'
            '</div>',
            src=obj.image.url,
            x=obj.image_focus_x, y=obj.image_focus_y, s=obj.image_scale,
            sf=f'{obj.image_scale:.1f}',
        )
    image_focus_editor.short_description = '焦點與縮放'


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
    
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status', 'series')
    list_editable = ('status',)
    ordering = ('title',)
    search_fields = ('title', 'title_zh', 'title_ch', 'IMDb_ID', 'aliases__title')

    list_filter = (
        ('year', DropdownFilter),
        ('status', ChoiceDropdownFilter),
        ('tags', RelatedDropdownFilter),
        ('series', RelatedDropdownFilter),
    )
    
    filter_horizontal = ('tags', 'studio')
    
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
            'fields': ('title', ('title_ch', 'title_zh'), 'description', 'trivia', 'videos')
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
            'fields': ('creators', 'studio', 'tags', 'series'),
        }),
    )

    filter_horizontal = ('creators', 'tags', 'studio')
    inlines = [CharacterInline, AliasInline, EpisodeInline]


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    form = NoAutocompleteModelForm
    list_display  = ('name', 'ani', 'va', 'image_preview')
    list_filter   = ('ani',)
    search_fields = ('name', 'name_zh', 'ani__title')
    ordering      = ('ani', 'order', 'name')
    readonly_fields = ('image_focus_editor',)

    fieldsets = (
        (None, {
            'fields': ('ani', 'order', 'name', 'name_zh', 'va', 'description'),
        }),
        ('圖片', {
            'fields': ('image', 'image_focus_editor',
                       'image_focus_x', 'image_focus_y', 'image_scale'),
        }),
    )

    class Media:
        js  = ('admin/js/char_image_editor.js',)
        css = {'all': ('admin/css/char_image_editor.css',)}

    def image_focus_editor(self, obj):
        if not obj.pk or not obj.image:
            return mark_safe('<p class="help" style="color:#888;font-style:italic;">'
                             '儲存圖片後即可使用視覺焦點編輯器</p>')
        return format_html(
            '<div class="char-focus-editor" '
            '     data-x="{x}" data-y="{y}" data-scale="{s}">'
            '  <div class="focus-preview-wrap">'
            '    <img src="{src}" alt="">'
            '    <div class="focus-dot"></div>'
            '    <div class="focus-hint">點擊設定焦點・滾輪縮放</div>'
            '  </div>'
            '  <div class="focus-zoom-row">'
            '    <label>縮放</label>'
            '    <input type="range" class="focus-scale-slider"'
            '           min="0.5" max="4" step="0.05" value="{s}">'
            '    <span class="focus-scale-val">{sf}×</span>'
            '  </div>'
            '</div>',
            src=obj.image.url,
            x=obj.image_focus_x, y=obj.image_focus_y, s=obj.image_scale,
            sf=f'{obj.image_scale:.1f}',
        )
    image_focus_editor.short_description = '焦點與縮放'

    def image_preview(self, obj):
        if not obj.image:
            return '無圖片'
        return format_html(
            '<div style="width:80px;height:100px;overflow:hidden;border-radius:4px;">'
            '<img src="{}" style="width:100%;height:100%;object-fit:cover;'
            'object-position:{}% {}%;transform:scale({});transform-origin:{}% {}%;">'
            '</div>',
            obj.image.url,
            obj.image_focus_x, obj.image_focus_y,
            obj.image_scale,
            obj.image_focus_x, obj.image_focus_y,
        )
    image_preview.short_description = '預覽'


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_works')
    ordering = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('creator_of', 'characters_voiced__ani')

    def display_works(self, obj):
        works = list(obj.creator_of.values_list('title', flat=True))
        va_works = list(obj.characters_voiced.values_list('ani__title', flat=True))
        all_works = list(dict.fromkeys(works + va_works))
        return ", ".join(all_works[:5]) + ("…" if len(all_works) > 5 else "")

    display_works.short_description = '參與作品'

admin.site.register(Tag)
admin.site.register(Studio)
admin.site.register(Episode)


class SeriesAdminForm(forms.ModelForm):
    works = forms.ModelMultipleChoiceField(
        queryset=Ani.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('作品', is_stacked=False),
        label='系列作品',
    )

    class Meta:
        model = Series
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['works'].initial = self.instance.works.all()


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    form = SeriesAdminForm
    list_display = ('name', 'work_count')
    search_fields = ('name',)

    def work_count(self, obj):
        return obj.works.count()
    work_count.short_description = '作品數量'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        selected = set(form.cleaned_data['works'].values_list('pk', flat=True))
        current = set(obj.works.values_list('pk', flat=True))

        # 觸發 Ani 的 pre_save/post_save 訊號，讓看板自動同步/合併邏輯正常運作
        for ani in Ani.objects.filter(pk__in=current - selected):
            ani.series = None
            ani.save()
        for ani in Ani.objects.filter(pk__in=selected - current):
            ani.series = obj
            ani.save()


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