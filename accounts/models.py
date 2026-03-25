from django.contrib.auth.models import AbstractUser
import os
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    avatar_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'avatars')
    avatar = models.CharField(
        max_length=50, 
        default='avatar_default.png',
        verbose_name="頭像"
    )
    class Meta:
        verbose_name = "會員"
        verbose_name_plural = "會員"

    def __str__(self):
        return self.username