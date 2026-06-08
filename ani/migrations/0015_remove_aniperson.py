from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ani', '0014_migrate_aniperson_to_creators'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ani',
            name='person',
        ),
        migrations.DeleteModel(
            name='AniPerson',
        ),
    ]
