# Generated by Django 4.1.7 on 2023-03-21 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0005_remove_sentence_lemmas_remove_sentence_words_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='text',
        ),
    ]
