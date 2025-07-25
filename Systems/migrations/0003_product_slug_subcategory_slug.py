# Generated by Django 5.2.4 on 2025-07-17 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Systems', '0002_category_slug_category_type_alter_category_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='subcategory',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]
