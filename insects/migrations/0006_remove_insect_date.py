# Generated by Django 3.2 on 2021-05-27 04:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('insects', '0005_new_image_is_valid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='insect',
            name='date',
        ),
    ]