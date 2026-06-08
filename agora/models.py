from django.conf import settings
from django.db import models

from ani.models import Ani


class Board(models.Model):
    name = models.CharField(max_length=50, verbose_name='看板名稱')
    name_zh = models.CharField(max_length=50, blank=True, null=True, verbose_name='看板名稱（繁中）')
    name_ch = models.CharField(max_length=50, blank=True, null=True, verbose_name='看板名稱（簡中）')
    anis = models.ManyToManyField(
        Ani, blank=True,
        related_name='boards', verbose_name='所屬作品'
    )
    description = models.TextField(blank=True, verbose_name='看板簡介')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '看板'
        verbose_name_plural = '看板列表'
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='posts', verbose_name='看板')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agora_posts', verbose_name='作者')
    title = models.CharField(max_length=100, blank=True, verbose_name='標題')
    content = models.TextField(blank=True, verbose_name='內容')
    image = models.ImageField(upload_to='agora_posts/', blank=True, null=True, verbose_name='圖片')

    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='replies', verbose_name='回覆對象'
    )
    root = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='thread_posts', verbose_name='所屬討論串'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '貼文'
        verbose_name_plural = '貼文列表'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.parent_id and not self.root_id:
            self.root = self.parent.root or self.parent
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.author}: {self.content[:30]}'
