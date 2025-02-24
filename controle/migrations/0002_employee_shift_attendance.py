# Generated by Django 5.1.6 on 2025-02-21 17:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controle', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='shift',
            field=models.CharField(choices=[('1', 'Turno 1'), ('2', 'Turno 2'), ('3', 'Turno 3')], default='1', max_length=1),
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('P', 'Presença'), ('F', 'Falta'), ('A', 'Atestado/Declaração'), ('N', 'Férias')], max_length=1)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='controle.employee')),
            ],
            options={
                'unique_together': {('employee', 'date')},
            },
        ),
    ]
