from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ani', '0012_add_trivia_field_remove_anitivia'),
    ]

    operations = [
        migrations.AddField(
            model_name='ani',
            name='creators',
            field=models.ManyToManyField(blank=True, related_name='creator_of', to='ani.person', verbose_name='主創'),
        ),
    ]
