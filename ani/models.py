from django.db import models

class Tag(models.Model):
    tag_name = models.CharField(max_length=50, verbose_name="標籤名稱")
    
    class Meta:
        verbose_name = "標籤"
        verbose_name_plural = "標籤庫"

    def __str__(self):
        return self.tag_name

# 2. 建立創作者/公司表
class Creator(models.Model):
    name = models.CharField(max_length=100, verbose_name="名稱")
    
    class Meta:
        verbose_name = "創作者"
        verbose_name_plural = "創作者庫"

    def __str__(self):
        return self.name

class Studio(models.Model):
    name = models.CharField(max_length=100, verbose_name="名稱")
    logo = models.ImageField(upload_to='logo/', blank=True, null=True, verbose_name="Logo")
    
    class Meta:
        verbose_name = "工作室/公司"
        verbose_name_plural = "工作室/公司庫"

    def __str__(self):
        return self.name
    
class Ani(models.Model):
    # 標題相關 (字串)
    title = models.CharField(max_length=200, verbose_name="英文標題")
    title_ch = models.CharField(max_length=200, blank=True, null=True, verbose_name="繁中標題")
    title_zh = models.CharField(max_length=200, blank=True, null=True, verbose_name="簡中標題")
    
    poster = models.ImageField(upload_to='posters/', blank=True, null=True, verbose_name="海報封面")
    banner = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="橫幅")
    
    # 外部 ID (字串)
    IMDb_ID = models.CharField(max_length=50, blank=True, null=True)
    
    # 數字類 (#)
    year = models.IntegerField(blank=True, null=True, verbose_name="年分")
    total_seasons = models.IntegerField(blank=True, null=True, verbose_name="總季數")
    total_episodes = models.IntegerField(blank=True, null=True, verbose_name="總集數")
    runtime = models.IntegerField(blank=True, null=True, verbose_name="單集時長")
    imdb_stars = models.FloatField(blank=True, null=True, verbose_name="IMDb評分") # 用 Float 是因為評分通常有小數點 (如 8.5)
    
    # 狀態與分級 (這裡先用字串存，未來可以進階改成下拉選單)
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name="狀態")
    rating = models.CharField(max_length=50, blank=True, null=True, verbose_name="分級")
    
    
    # 關聯類 (你的截圖裡有 ↗ 箭頭，這代表關聯。為了新手好上手，我們先用 CharField 存文字，未來再教你怎麼改成獨立資料表關聯)
    studio = models.ManyToManyField(Studio, verbose_name="工作室/公司")
    tags = models.ManyToManyField(Tag, verbose_name="標籤")
    creators = models.ManyToManyField(Creator, verbose_name="創作者")
    
    class Meta:
        verbose_name = "動畫"
        verbose_name_plural = "動畫庫"

    def __str__(self):
        return self.title