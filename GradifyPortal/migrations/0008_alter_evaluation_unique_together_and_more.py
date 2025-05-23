# Generated by Django 5.1.6 on 2025-04-14 16:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GradifyPortal', '0007_alter_coordinator_password_alter_mentor_password_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='evaluation',
            unique_together={('submission', 'evaluated_by_coordinator')},
        ),
        migrations.AlterField(
            model_name='coordinator',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$870000$6tJCNMk7SFPGEnCQxkBypX$tcdIcWRXZCj47/2xasOx5Z1UGhypMsIBnHEwliq2If0=', max_length=128),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GradifyPortal.submission'),
        ),
        migrations.AlterField(
            model_name='mentor',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$870000$AOBe3ABIft0C1CKOHC7Mec$caoJCgKVOGnURNL9AfjzOJLmkFAdlogfLqarZkbmMUU=', max_length=128),
        ),
        migrations.AlterField(
            model_name='student',
            name='password',
            field=models.CharField(default='pbkdf2_sha256$870000$1AzvBjoQJjoPXt37ZAGcNU$tls0ixOKcmd9lehslfdslNGkGT4pi4lIHvfkq4qzvGs=', max_length=128),
        ),
        migrations.AlterUniqueTogether(
            name='evaluation',
            unique_together={('submission', 'evaluated_by_coordinator'), ('submission', 'evaluated_by_mentor')},
        ),
    ]
