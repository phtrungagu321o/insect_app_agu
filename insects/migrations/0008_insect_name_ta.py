# Generated by Django 3.2.3 on 2022-03-23 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('insects', '0007_filesadmin'),
    ]

    operations = [
        migrations.AddField(
            model_name='insect',
            name='name_TA',
            field=models.CharField(default='null', max_length=100),
        ),
    ]