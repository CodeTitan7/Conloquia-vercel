# Generated by Django 5.0.7 on 2024-08-26 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailer', '0008_alter_email_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, default='profile_pics/default.png', null=True, upload_to='profile_pics/'),
        ),
    ]
