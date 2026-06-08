from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ani', '0015_remove_aniperson'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='image_focus_x',
            field=models.FloatField(default=50.0, verbose_name='圖片焦點 X%'),
        ),
        migrations.AddField(
            model_name='character',
            name='image_focus_y',
            field=models.FloatField(default=20.0, verbose_name='圖片焦點 Y%'),
        ),
        migrations.AddField(
            model_name='character',
            name='image_scale',
            field=models.FloatField(default=1.0, verbose_name='圖片縮放倍率'),
        ),
    ]
