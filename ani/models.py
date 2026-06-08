import os
import re
from django.db import models
from django.conf import settings
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def _char_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', instance.name)
    return f'characters/{instance.ani_id}_{safe_name}{ext}'


_YOUTUBE_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{6,})'
)
_BILIBILI_RE = re.compile(r'bilibili\.com/video/(BV[A-Za-z0-9]+)')


def _video_embed_url(url):
    if not url:
        return None
    m = _YOUTUBE_RE.search(url)
    if m:
        return f'https://www.youtube.com/embed/{m.group(1)}'
    m = _BILIBILI_RE.search(url)
    if m:
        return f'https://player.bilibili.com/player.html?bvid={m.group(1)}&autoplay=0'
    return None

class Tag(models.Model):
    tag_name = models.CharField(max_length=50, verbose_name="標籤名稱")
    
    class Meta:
        verbose_name = "標籤"
        verbose_name_plural = "標籤庫"

    def __str__(self):
        return self.tag_name

class Person(models.Model):
    name = models.CharField(max_length=100, verbose_name="名稱")

    class Meta:
        verbose_name = "人員"
        verbose_name_plural = "人員庫"

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
    
class Series(models.Model):
    name = models.CharField(max_length=200, verbose_name="系列名稱")
    name_zh = models.CharField(max_length=200, blank=True, null=True, verbose_name="繁中名稱")
    name_ch = models.CharField(max_length=200, blank=True, null=True, verbose_name="簡中名稱")
    description = models.TextField(blank=True, null=True, verbose_name="系列簡介")

    class Meta:
        verbose_name = "系列"
        verbose_name_plural = "系列庫"

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
    trivia      = models.TextField(blank=True, null=True, verbose_name="瑣事")
    videos      = models.TextField(
        blank=True, null=True, verbose_name="影片",
        help_text="每行一個 YouTube 或 Bilibili 連結，可選擇用「|」加上標題，例如：https://youtu.be/xxxx | PV預告"
    )
    
    studio   = models.ManyToManyField(Studio, blank=True, verbose_name="工作室/公司")
    tags     = models.ManyToManyField(Tag, blank=True, verbose_name="標籤")
    creators = models.ManyToManyField('Person', blank=True, related_name='creator_of', verbose_name="主創")
    series   = models.ForeignKey(
        Series, blank=True, null=True, on_delete=models.SET_NULL,
        related_name='works', verbose_name="所屬系列"
    )

    class Meta:
        verbose_name = "動畫"
        verbose_name_plural = "動畫庫"

    def __str__(self):
        return self.title

    @property
    def series_name(self):
        return self.series.name if self.series else self.title

    @property
    def series_name_zh(self):
        return self.series.name_zh if self.series else self.title_zh

    @property
    def series_name_ch(self):
        return self.series.name_ch if self.series else self.title_ch

    @property
    def video_embeds(self):
        embeds = []
        for line in (self.videos or '').splitlines():
            line = line.strip()
            if not line:
                continue
            url, _, title = line.partition('|')
            embed_url = _video_embed_url(url.strip())
            if embed_url:
                embeds.append({'embed_url': embed_url, 'title': title.strip()})
        return embeds


class Character(models.Model):
    ani      = models.ForeignKey(Ani, on_delete=models.CASCADE, related_name='characters')
    name     = models.CharField(max_length=100, verbose_name="名稱")
    name_zh  = models.CharField(max_length=100, blank=True, null=True, verbose_name="中文名稱")
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    image         = models.ImageField(upload_to=_char_image_path, blank=True, null=True, verbose_name="圖片")
    image_focus_x = models.FloatField(default=50.0, verbose_name="圖片焦點 X%")
    image_focus_y = models.FloatField(default=20.0, verbose_name="圖片焦點 Y%")
    image_scale   = models.FloatField(default=1.0,  verbose_name="圖片縮放倍率")
    va       = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='characters_voiced', verbose_name="聲優")
    order    = models.PositiveSmallIntegerField(default=0, verbose_name="排序")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "角色"
        verbose_name_plural = "角色庫"

    def __str__(self):
        return f"{self.ani.title} — {self.name}"



class AniAlias(models.Model):
    ani = models.ForeignKey(Ani, on_delete=models.CASCADE, related_name='aliases')
    title = models.CharField(max_length=200, verbose_name="別名")
    source = models.CharField(max_length=100, blank=True, null=True, verbose_name="來源")

    class Meta:
        verbose_name = "別名"
        verbose_name_plural = "別名庫"

    def __str__(self):
        return f"{self.ani.title} - {self.title}"


class SyncJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', '等待中'
        RUNNING = 'RUNNING', '執行中'
        DONE    = 'DONE',    '完成'
        ERROR   = 'ERROR',   '錯誤'

    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    progress   = models.IntegerField(default=0)
    total      = models.IntegerField(default=0)
    log        = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "同步任務"
        verbose_name_plural = "同步任務紀錄"
        ordering = ['-created_at']

    def __str__(self):
        return f"SyncJob #{self.pk} [{self.status}] {self.progress}/{self.total}"

    @property
    def progress_pct(self):
        return int(self.progress / self.total * 100) if self.total else 0


class UserReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    ani  = models.ForeignKey(Ani, on_delete=models.CASCADE, related_name='reviews')
    score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–10, optional
    text = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'ani')
        ordering = ['-updated_at']
        verbose_name = "評分與評論"
        verbose_name_plural = "評分與評論"

    def __str__(self):
        return f"{self.user} → {self.ani.title}"


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