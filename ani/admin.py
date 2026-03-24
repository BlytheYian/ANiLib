from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html
from django.core.files.base import ContentFile
import os
from io import BytesIO
from PIL import Image
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter

from .models import Ani, Tag, Creator, Studio, Episode

class NoAutocompleteModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'

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
    
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status')
    list_editable = ('status',)
    ordering = ('title',) 
    search_fields = ('title', 'title_zh', 'title_ch', 'IMDb_ID')
    
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

    readonly_fields = ['poster_preview', 'banner_preview']
    
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
    
    inlines = [EpisodeInline]

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