from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

class Tag(models.Model):
    tag_name = models.CharField(max_length=50, verbose_name="標籤名稱")
    
    class Meta:
        verbose_name = "標籤"
        verbose_name_plural = "標籤庫"

    def __str__(self):
        return self.tag_name

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
    title = models.CharField(max_length=200, verbose_name="英文標題")
    title_ch = models.CharField(max_length=200, blank=True, null=True, verbose_name="簡中標題")
    title_zh = models.CharField(max_length=200, blank=True, null=True, verbose_name="繁中標題")
    
    poster = models.ImageField(upload_to='posters/', blank=True, null=True, verbose_name="海報封面")
    banner = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="橫幅")
    poster_thumbnail = ImageSpecField(
        source='poster',
        processors=[ResizeToFit(504, 840)], 
        format='WEBP',
        options={'quality': 90}
    )
    
    IMDb_ID = models.CharField(max_length=50, blank=True, null=True)
    
    year = models.IntegerField(blank=True, null=True, verbose_name="年分")
    total_seasons = models.IntegerField(blank=True, null=True, verbose_name="總季數")
    total_episodes = models.IntegerField(blank=True, null=True, verbose_name="總集數")
    runtime = models.IntegerField(blank=True, null=True, verbose_name="單集時長")
    imdb_stars = models.FloatField(blank=True, null=True, verbose_name="IMDb評分")
    
    class StatusChoices(models.TextChoices):
        CROWDFUNDING = 'CROWDFUNDING', '募資中'
        PILOT = 'PILOT', '試播集'
        UPCOMING = 'UPCOMING', '即將上映'
        GREENLIGHT = 'GREENLIGHT', '確認製作'
        ONGOING = 'ONGOING', '連載中'
        PAUSED = 'PAUSED', '暫停更新'
        FINISHED = 'FINISHED', '已完結'
        CANCELLED = 'CANCELLED', '已取消'
        UNKNOWN = 'UNKNOWN', '未知狀態'
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices,
        default=StatusChoices.ONGOING,
        blank=True, 
        null=True, 
        verbose_name="狀態"
    )
    rating = models.CharField(max_length=50, blank=True, null=True, verbose_name="分級")
    
    description = models.TextField(blank=True, null=True, verbose_name="簡介")
    
    studio = models.ManyToManyField(Studio, verbose_name="工作室/公司")
    tags = models.ManyToManyField(Tag, verbose_name="標籤")
    creators = models.ManyToManyField(Creator, verbose_name="創作者")
    
    class Meta:
        verbose_name = "動畫"
        verbose_name_plural = "動畫庫"
    def __str__(self):
        return self.title

class Episode(models.Model):
    ani = models.ForeignKey(Ani, on_delete=models.CASCADE, related_name='episodes')
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="名稱")
    season = models.CharField(max_length=20, blank=True, null=True, verbose_name="季數")
    number = models.CharField(max_length=20, verbose_name="集數") 
    release_time = models.DateTimeField(verbose_name="更新時間")
    
    class Meta:
        ordering = ['release_time']
        verbose_name = "集數"
        verbose_name_plural = "劇集庫"

    def __str__(self):
        season_str = f" {self.season}" if self.season else ""
        title_str = f" - {self.title}" if self.title else ""
        return f"{self.ani.title} - {season_str}{self.number.zfill(2)}{title_str}"