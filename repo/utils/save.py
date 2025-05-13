from django.db import IntegrityError
from repo.models import Game, Player

def save_game_data(game_data, stdout_writer, source_info=""):
    """
    Saves a single game's data to the database.
    Handles IntegrityError by skipping and logs other errors.
    """
    try:
        Game.objects.create(**game_data)
        return 'created'
    except IntegrityError:
        # Game with this pgn_hash likely already exists, skip silently (although it should not happen often as we are using redis cache now to check while processing PGN if it already exists in the database)
        return 'skipped'
    except Exception as e:
        error_message = f"Error saving game"
        if source_info:
            error_message += f" from {source_info}"
        error_message += f": {e} - Data: {game_data}"
        # Ensure stdout_writer has style attribute, typical for Django commands
        if hasattr(stdout_writer, 'style') and hasattr(stdout_writer.style, 'ERROR'):
            stdout_writer.write(stdout_writer.style.ERROR(error_message))
        else: # Fallback if style is not available (e.g. plain print)
            print(f"ERROR: {error_message}")
        return 'error'
    
def get_or_create_chesscom_player(username):
    from repo.utils.chesscom.api import CHESSCOM_API
    player, created = Player.objects.get_or_create(chesscom_username=username)

    # Only fetch details if newly created or missing name
    if created or not player.name:
        try:
            chesscom_api = CHESSCOM_API()
            player_data = chesscom_api.get_player_profile(username)
            player.name = player_data.get('name', '')
            player.country = player_data.get('country', '').split('/')[-1] if player_data.get('country') else None
            player.title = player_data.get('title', '')
            player.save()
        except Exception as e:
            print(f"Failed to fetch data for {username}: {e}")

    return player


def get_or_create_lichess_player(fide_id):
    from repo.utils.lichess.api import LICHESS_API
    player, created = Player.objects.get_or_create(fide_id=fide_id)
    # Only fetch details if newly created or missing name
    if created or not player.name:
        try:
            lichess_api = LICHESS_API()
            player_data = lichess_api.get_player_fide_profile(fide_id)
            player.name = player_data.get('name', '')
            player.fide_id = fide_id
            player.country = player_data.get('federation', '')
            player.title = player_data.get('title', '')
            player.save()
        except Exception as e:
            print(f"Failed to fetch data for {fide_id}: {e}")
    return player
