from django.db import migrations


def forward(apps, schema_editor):
    AniPerson = apps.get_model('ani', 'AniPerson')
    for entry in AniPerson.objects.filter(role='CREATOR').select_related('ani', 'person'):
        entry.ani.creators.add(entry.person)


def backward(apps, schema_editor):
    Ani = apps.get_model('ani', 'Ani')
    for ani in Ani.objects.prefetch_related('creators'):
        ani.creators.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('ani', '0013_add_creators_m2m'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
