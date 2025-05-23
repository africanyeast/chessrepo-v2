# Generated by Django 5.2.1 on 2025-05-12 22:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("repo", "0007_remove_game_games_source_2baaef_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Player",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "fide_id",
                    models.CharField(blank=True, max_length=50, null=True, unique=True),
                ),
                ("country", models.CharField(blank=True, max_length=100, null=True)),
                ("title", models.CharField(blank=True, max_length=10, null=True)),
                (
                    "chesscom_username",
                    models.CharField(
                        blank=True, max_length=100, null=True, unique=True
                    ),
                ),
                (
                    "lichess_username",
                    models.CharField(
                        blank=True, max_length=100, null=True, unique=True
                    ),
                ),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Player",
                "verbose_name_plural": "Players",
                "db_table": "players",
                "ordering": ["name"],
            },
        ),
        migrations.RenameIndex(
            model_name="game",
            new_name="games_white_i_f97198_idx",
            old_name="games_white_2e28f8_idx",
        ),
        migrations.RenameIndex(
            model_name="game",
            new_name="games_black_i_fd5074_idx",
            old_name="games_black_754b7d_idx",
        ),
        migrations.AddField(
            model_name="game",
            name="black_username",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="game",
            name="white_username",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="game",
            name="black",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="black_games",
                to="repo.player",
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="white",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="white_games",
                to="repo.player",
            ),
        ),
    ]
