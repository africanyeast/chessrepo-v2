import time
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from repo.utils.lichess.api import LICHESS_API
from repo.utils.pgn import extract_games_from_pgn_string
from repo.utils.save import save_game_data
from repo.models import Game

class Command(BaseCommand):
    help = 'Fetches new games from Lichess broadcasts (Tier 5 finished rounds) and stores them in the database.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to fetch games from Lichess broadcasts...")

        lichess_api = LICHESS_API()
        source = "lichess"
        api_call_delay = 1  # Delay in seconds between API calls

        games_newly_saved_count = 0
        games_skipped_count = 0
        games_error_count = 0

        try:
            top_broadcasts_data = lichess_api.get_broadcast_top()
            time.sleep(api_call_delay) # Delay after API call
        except Exception as e:
            raise CommandError(f"Failed to fetch top broadcasts from Lichess: {e}")

        if not top_broadcasts_data:
            self.stdout.write(self.style.WARNING("Could not fetch top broadcasts data from Lichess or data was empty."))
            return

        try:
            round_ids = lichess_api.get_finished_rounds_from_top_broadcast(top_broadcasts_data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing top broadcasts data: {e}"))
            return
            
        if not round_ids:
            self.stdout.write(self.style.NOTICE("No finished Tier 5 rounds found in Lichess top broadcasts on this run."))
            return

        self.stdout.write(f"Found {len(round_ids)} finished Tier 5 Lichess rounds to process.")

        for round_id in round_ids:
            try:
                round_pgn = lichess_api.get_round_pgn(round_id)
                time.sleep(api_call_delay) # Delay after API call
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to fetch PGN for round {round_id}: {e}"))
                continue

            if not round_pgn:
                self.stdout.write(self.style.NOTICE(f"  No PGN data fetched for round {round_id}."))
                continue

            try:
                games_from_pgn = extract_games_from_pgn_string(round_pgn, source)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error extracting games from PGN for round {round_id}: {e}"))
                continue
            
            if not games_from_pgn:
                self.stdout.write(self.style.NOTICE(f"  No games extracted from PGN for round {round_id}."))
                continue
            
            self.stdout.write(f"  Extracted {len(games_from_pgn)} games from round {round_id}.")

            for game_data in games_from_pgn:
                status = save_game_data(game_data, self.stdout, f"lichess round {round_id}")
                if status == 'created':
                    games_newly_saved_count += 1
                elif status == 'skipped':
                    games_skipped_count += 1
                elif status == 'error':
                    games_error_count += 1
            
        self.stdout.write(self.style.SUCCESS(
            f"\nFinished lichess run. "
            f"Newly saved: {games_newly_saved_count}, Skipped: {games_skipped_count}, Errors: {games_error_count}."
        ))