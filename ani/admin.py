from django.contrib import admin
from .models import Ani, Tag, Creator, Studio

# Register your models here.
@admin.register(Ani)
class AniAdmin(admin.ModelAdmin):
    # 1. 決定要在列表顯示哪些欄位（這會讓這些欄位變成可點擊的排序按鈕）
    list_display = ('title', 'title_zh', 'title_ch', 'year', 'imdb_stars', 'status')
    
    # 2. 設定進入頁面時的預設排序
    ordering = ('title',) 
    
    # 3. 額外加碼：增加搜尋功能，讓後端更像一個真正的資料庫管理系統
    search_fields = ('title', 'title_zh', 'title_ch', 'IMDb_ID')
    
    # 4. 額外加碼：右側過濾器 (按年分或狀態過濾)
    list_filter = ('year', 'status', 'tags')
    
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
    
admin.site.register(Tag)
admin.site.register(Studio)