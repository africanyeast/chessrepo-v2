# Generated by Django 5.2.1 on 2025-05-15 22:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("repo", "0010_remove_game_games_date_a10f30_idx_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="game",
            name="games_endtime_c7faad_idx",
        ),
    ]
