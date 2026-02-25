from django.contrib import admin
from .models import Ani, Tag, Creator, Studio

# Register your models here.
admin.site.register(Ani)
admin.site.register(Tag)
admin.site.register(Creator)
admin.site.register(Studio)