from django.db import IntegrityError
from repo.models import Game

def save_game_data(game_data, stdout_writer, source_info=""):
    """
    Saves a single game's data to the database.
    Handles IntegrityError by skipping and logs other errors.
    """
    try:
        Game.objects.create(**game_data)
        return 'created'
    except IntegrityError:
        # Game with this pgn_hash likely already exists, skip silently
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
