from django.contrib import admin
from .models import Ani, Tag, Creator, Studio
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter
import os
from io import BytesIO
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile

# Register your models here.

@admin.register(Ani)
class AniAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status')

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
            # format_html：Django 為了安全，預設會把所有字串當成純文字。如果不使用這個函數，頁面上會直接顯示 <img src="..."> 這串程式碼，而不是圖片。
            return format_html('<img src="{}" style="width: 150px; height: auto; border-radius: 5px; shadow: 2px 2px 5px rgba(0,0,0,0.3);" />', obj.poster.url)
        return "尚未上傳海報"

    def banner_preview(self, obj):
        if obj.banner:
            # 橫幅可以設寬一點
            return format_html('<img src="{}" style="width: 300px; height: auto; border-radius: 5px;" />', obj.banner.url)
        return "尚未上傳橫幅"

    poster_preview.short_description = "海報預覽"
    banner_preview.short_description = "橫幅預覽"

    # 必須加入 readonly_fields，否則 Django 不會執行這個函數
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
    
    
    
class AniInline(admin.TabularInline):
    model = Ani.creators.through
    extra = 1
    verbose_name = "參與的動畫"
    verbose_name_plural = "參與的動畫列表"
@admin.register(Creator)
class CreatorAdmin(admin.ModelAdmin):
    list_display = ('name','display_animations')
    inlines = [AniInline]
    ordering = ('name',) 
    def display_animations(self, obj):
        # 透過反向查詢 ani_set 取得所有關聯的動畫標題
        return ", ".join([ani.title for ani in obj.ani_set.all()])
    
    display_animations.short_description = '參與作品'
    
'''將 Model (Creator) 與其配置類 (CreatorAdmin) 綁在一起, 和上面是一樣的
admin.site.register(Creator, CreatorAdmin)'''
    
admin.site.register(Tag)
admin.site.register(Studio)