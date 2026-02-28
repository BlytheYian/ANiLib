from django.contrib import admin
from .models import Ani, Tag, Creator, Studio
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter

# Register your models here.
@admin.register(Ani)
class AniAdmin(admin.ModelAdmin):
    # 1. 決定要在列表顯示哪些欄位（這會讓這些欄位變成可點擊的排序按鈕）
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status')
    
    # 2. 設定進入頁面時的預設排序
    ordering = ('title',) 
    
    # 3. 額外加碼：增加搜尋功能，讓後端更像一個真正的資料庫管理系統
    search_fields = ('title', 'title_zh', 'title_ch', 'IMDb_ID')
    
    list_filter = (
        # 1. 普通欄位（如年份）使用 DropdownFilter
        ('year', DropdownFilter),
        # 2. 有 choices 的 CharField 使用 ChoiceDropdownFilter
        ('status', ChoiceDropdownFilter),
        # 3. 多對多或外鍵關聯（如標籤）使用 RelatedDropdownFilter
        ('tags', RelatedDropdownFilter),
    )
    
    filter_horizontal = ('creators', 'tags', 'studio')
    
    def poster_preview(self, obj):
        if obj.poster:
            # 這裡設定縮圖的寬度，高度會按比例縮放
            # format_html：Django 為了安全，預設會把所有字串當成純文字。如果不使用這個函數，頁面上會直接顯示 <img src="..."> 這串程式碼，而不是圖片。
            return format_html('<img src="{}" style="width: 150px; height: auto; border-radius: 5px; shadow: 2px 2px 5px rgba(0,0,0,0.3);" />', obj.poster.url)
        return "尚未上傳海報"

    def banner_preview(self, obj):
        if obj.banner:
            # 橫幅可以設寬一點
            return format_html('<img src="{}" style="width: 300px; height: auto; border-radius: 5px;" />', obj.banner.url)
        return "尚未上傳橫幅"

    # 2. 為預覽函數設定在後端顯示的名稱
    poster_preview.short_description = "海報預覽"
    banner_preview.short_description = "橫幅預覽"

    # 3. 關鍵：必須加入 readonly_fields，否則 Django 不會執行這個函數
    readonly_fields = ['poster_preview', 'banner_preview']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', ('title_ch', 'title_zh'), 'description')
        }),
        ('視覺素材', {
            'fields': (
                'poster', 'poster_preview',  # 原本的上傳欄位與預覽並列
                'banner', 'banner_preview'
            ),
            'classes': ('collapse',), # 預設折疊，點擊展開
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
    
# 因為 creators 是定義在 Ani 模型中的 ManyToManyField
# 我們要在 Creator 這裡顯示，要指向 Ani 模型的 through（中間表）
class AniInline(admin.TabularInline):
    model = Ani.creators.through  # 指向多對多中間表
    extra = 1                     # 預設多顯示一個空白列供新增
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
    
'''class CreatorAdmin(admin.ModelAdmin):
    pass

# 顯式連結：將 Model (Creator) 與其配置類 (CreatorAdmin) 綁在一起, 和上面是一樣的
admin.site.register(Creator, CreatorAdmin)'''
    
admin.site.register(Tag)
admin.site.register(Studio)