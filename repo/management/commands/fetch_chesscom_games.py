import json
import os
import re
import hashlib
import io
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import IntegrityError
import chess
import chess.pgn
from repo.utils.chesscom.api import CHESSCOM_API
from repo.utils.pgn import pgn_to_dict, extract_games_from_pgn_string
from repo.models import Game
from decouple import config

# Path to your players JSON file. Consider making this a command argument or a Django setting.
# For now, let's assume it's relative to the Django project's base directory (where manage.py is)
DEFAULT_PLAYERS_FILE_PATH = os.path.join(settings.BASE_DIR, config('PLAYERS_JSON_PATH'))

class Command(BaseCommand):
    help = 'Fetches new games from Chess.com for configured players and stores them in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--players_file',
            type=str,
            default=DEFAULT_PLAYERS_FILE_PATH,
            help='Path to the JSON file containing player usernames.'
        )

    def handle(self, *args, **options):
        players_file = options['players_file']
        self.stdout.write(f"Using players file: {players_file}")

        try:
            with open(players_file, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Players file not found at {players_file}")
        except json.JSONDecodeError:
            raise CommandError(f"Error decoding JSON from {players_file}")

        usernames = [
            p['chesscom_username'] for p in players_data if isinstance(p, dict) and p.get('chesscom_username')
        ]
        if not usernames:
            self.stdout.write(self.style.WARNING("No Chess.com usernames found in the players file."))
            return

        chesscom_api = CHESSCOM_API()
        source = "chesscom"

        for username in usernames:
            user_pgn = chesscom_api.get_player_games_current_month_pgn(username) # Assumes API takes only username

            if not user_pgn:
                #self.stdout.write(self.style.NOTICE(f"  No PGN data fetched for {username} for the current month."))
                continue

            games_from_pgn = extract_games_from_pgn_string(user_pgn, source)

            for game_dict in games_from_pgn:
                    try:
                        Game.objects.create(**game_dict)
                    except IntegrityError: # Should be rare if hash check is robust
                        self.stdout.write(self.style.WARNING(f"  IntegrityError: Game with hash {game_dict.get("pgn_hash")} might already exist (race condition?) or other constraint violation."))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Error saving game for {username}: {e} - Data: {game_dict}"))
            
            #time.sleep(0.5) # Be polite to the API

        self.stdout.write(self.style.SUCCESS(f"\nFinished run."))
