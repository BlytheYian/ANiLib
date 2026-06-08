from django.db import migrations


def forward(apps, schema_editor):
    Creator  = apps.get_model('ani', 'Creator')
    Person   = apps.get_model('ani', 'Person')
    AniPerson = apps.get_model('ani', 'AniPerson')

    creator_to_person = {}
    for c in Creator.objects.all():
        p, _ = Person.objects.get_or_create(name=c.name)
        creator_to_person[c.pk] = p

    for c in Creator.objects.prefetch_related('ani_set'):
        p = creator_to_person[c.pk]
        for ani in c.ani_set.all():
            AniPerson.objects.get_or_create(ani=ani, person=p, role='CREATOR')


def backward(apps, schema_editor):
    AniPerson = apps.get_model('ani', 'AniPerson')
    AniPerson.objects.filter(role='CREATOR').delete()
    apps.get_model('ani', 'Person').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ani', '0008_person_aniperson'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
