# Generated by Django 5.2.1 on 2025-05-13 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NutriBite', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('ingredients', models.TextField(help_text='List one ingredient per line')),
                ('preparation', models.TextField()),
            ],
        ),
    ]
