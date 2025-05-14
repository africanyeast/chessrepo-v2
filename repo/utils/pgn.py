import re
import chess
import chess.pgn
import hashlib
import io
from django.core.cache import cache
from repo.utils.save import get_or_create_chesscom_player, get_or_create_lichess_player


def extract_opening_from_chesscom_ecourl(eco_url: str | None) -> str:
        """Extracts opening name from ECOUrl."""
        if not eco_url:
            return ""
        # Example: "https://www.chess.com/openings/Reti-Opening-Pirc-Invitation"
        # The value might have leading/trailing spaces or be quoted in PGN
        eco_url = eco_url.strip().strip('"')
        match = re.search(r'/openings/([^/?]+)', eco_url)
        if match:
            return match.group(1).replace('-', ' ') # replace hyphens with spaces for readability
        return ""
# extracting tournament name from the tournament headers
# an example: https://www.chess.com/tournament/live/late-titled-tuesday-blitz-may-06-2025-5632457
# the tournament name is "Late-Titled Tuesday Blitz" remove the date, url, and id
# But if tournament is not titled tuesday or freestyle friday, use whatever is passed in the headers directly
def extract_chesscom_tournament_name(tournament_header):
   
    if not tournament_header:
        return ""
        
    tournament_name = tournament_header
    
    # Extract just the tournament name from the URL if it's a chess.com URL
    if "chess.com/tournament" in tournament_name:
        tournament_name = tournament_name.split("/")[-1]
    # Replace hyphens with spaces
    tournament_name = tournament_name.replace("-", " ")
    
    # Remove date patterns
    # Handle various date formats
    date_patterns = [
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[- ]\d{2}[- ]\d{4}',  # may-06-2025
        r'\d{4}[- ]\d{2}[- ]\d{2}',  # 2025-05-06
        r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}',  # may 2025
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}',  # may 2025
        r'\s+\d{4}\s*$',  # trailing year
        r'\s+20\d{2}\s*$'  # trailing 20XX year
    ]
    
    for pattern in date_patterns:
        tournament_name = re.sub(pattern, '', tournament_name, flags=re.IGNORECASE)
    
    # Remove numeric IDs at the end (common in chess.com URLs)
    tournament_name = re.sub(r'\s+\d+\s*$', '', tournament_name)
    
    # Clean up special characters and multiple spaces
    tournament_name = re.sub(r'[^\w\s]', ' ', tournament_name)  # Replace special chars with space
    tournament_name = re.sub(r'\s+', ' ', tournament_name)  # Normalize spaces
    
    # Title case the tournament name for consistency
    tournament_name = tournament_name.title()
    
    return tournament_name.strip()


def generate_pgn_hash(pgn_string: str) -> str:
        return hashlib.sha256(pgn_string.encode('utf-8')).hexdigest()

def determine_game_format(pgn_string: str) -> str | None:
        """
        Determines the game format (bullet, blitz, rapid, classical) based on the clock annotation
        in the first move of the PGN.
        
        Returns:
            str | None: The game format or None if no clock annotation is found
        """
        # Look for the first clock annotation in the PGN
        clock_match = re.search(r'\[%clk\s+(\d+):(\d+):(\d+)(?:\.\d+)?\]', pgn_string)
        
        if not clock_match:
            return None
            
        # Extract hours, minutes, seconds
        hours = int(clock_match.group(1))
        minutes = int(clock_match.group(2))
        seconds = int(clock_match.group(3))
        
        # Calculate total time in minutes
        total_minutes = hours * 60 + minutes + (seconds / 60)
        
        # Determine format based on time
        if total_minutes < 3:
            return "bullet"
        elif total_minutes < 10:
            return "blitz"
        elif total_minutes <= 15:
            return "rapid"
        else:
            return "classical"

# check if a pgn_string is already potentially in the database (at least cached in redis)
# if pgn hash is a key in the redis cache, return False
# if pgn hash is not a key in the redis cache, add it to the redis cache and return True
def is_new_game(pgn_string: str) -> bool:
    pgn_hash = generate_pgn_hash(pgn_string)
    if cache.get(pgn_hash):
        return False
    cache.set(pgn_hash, True, timeout=60 * 60 * 24 * 32)  # 32 days TTL
    return pgn_hash

def pgn_to_dict(pgn_string: str, source: str, pgn_hash: str) -> dict:
        """Converts a chess.pgn.Game object to a standardized dictionary."""
        game = chess.pgn.read_game(io.StringIO(pgn_string))
        headers = game.headers
        # Determine game format
        game_format = determine_game_format(pgn_string)
        
        if source=="chesscom":
            
            white_username = headers.get("White", "")
            black_username = headers.get("Black", "")
            white_player = get_or_create_chesscom_player(white_username)
            black_player = get_or_create_chesscom_player(black_username)

            if headers.get("Opening"):
                opening_name = headers.get("Opening", "")
            elif headers.get("ECOUrl"):
                opening_name = extract_opening_from_chesscom_ecourl(headers.get("ECOUrl"))
            else:
                opening_name = ""
            # extracting tournament name from the tournament headers
            tournament_name = ""
            if headers.get("Tournament"):
                tournament_name = extract_chesscom_tournament_name(headers.get("Tournament"))
            else:
                # fallback to Event if tournament is not available
                tournament_name = extract_tournament_name(headers.get("Event", ""))
            
            return {
                "white": white_player,
                "black": black_player,
                "white_username": white_username,
                "black_username": black_username,
                "result": headers.get("Result", ""),
                "opening": opening_name,
                "eco": headers.get("ECO", ""),
                "whiteelo": headers.get("WhiteElo", ""),
                "blackelo": headers.get("BlackElo", ""),
                "event": headers.get("Event", ""),
                "site": headers.get("Site", ""),
                "tournament": tournament_name,
                "round": headers.get("Round", ""),
                "date": headers.get("Date", ""), # Assuming chess.com dates are usually well-formed or handled by model
                "enddate": headers.get("EndDate", headers.get("Date", "")), # Fallback to Date if EndDate is missing
                "endtime": headers.get("EndTime", ""),
                "timecontrol": headers.get("TimeControl", ""),
                "variant": headers.get("Variant", ""),
                "link": headers.get("Link", ""),
                "format": game_format,
                "pgn": pgn_string,
                "pgn_hash": pgn_hash,
                "source": source,
            }
        elif source=="lichess":
            
            def clean_pgn_value(value: str | None, type: str = "date") -> str | None:
                """Helper to clean PGN date/time values. Returns None if invalid."""
                if value is None or value == "" or "?" in value:
                    return None
                return value

            raw_pgn_date = headers.get("Date")
            raw_pgn_utc_date = headers.get("UTCDate")
            raw_pgn_utc_time = headers.get("UTCTime")

            cleaned_date = clean_pgn_value(raw_pgn_date, "date")
            cleaned_utc_date = clean_pgn_value(raw_pgn_utc_date, "date")
            cleaned_utc_time = clean_pgn_value(raw_pgn_utc_time, "time")

            # Determine final date for the model
            # Prioritize "Date" header if valid, otherwise fallback to "UTCDate" if valid.
            final_model_date = cleaned_date if cleaned_date else cleaned_utc_date

            # Determine final enddate for the model
            # Prioritize "UTCDate" if valid, otherwise fallback to the determined final_model_date.
            final_model_enddate = cleaned_utc_date if cleaned_utc_date else final_model_date
            
            # final_model_endtime is simply the cleaned_utc_time
            final_model_endtime = cleaned_utc_time

            white_fide_id = headers.get("WhiteFideId", "")
            black_fide_id = headers.get("BlackFideId", "")
            white_player = get_or_create_lichess_player(white_fide_id)
            black_player = get_or_create_lichess_player(black_fide_id)

            return {
                "white": white_player,
                "black": black_player,
                "white_username": headers.get("White", ""),
                "black_username": headers.get("Black", ""),
                "result": headers.get("Result", ""),
                "opening": headers.get("Opening", ""),
                "eco": headers.get("ECO", ""),
                "whiteelo": headers.get("WhiteElo", ""),
                "blackelo": headers.get("BlackElo", ""),
                "event": headers.get("Event", ""), # Lichess PGNs use "Event" for the tournament/event name
                "site": headers.get("Site", ""),
                "tournament": headers.get("Event", ""), # Using Event as Tournament for Lichess
                "round": headers.get("Round", ""),
                "date": final_model_date,
                "enddate": final_model_enddate,
                "endtime": final_model_endtime,
                "variant": headers.get("Variant", ""),
                "link": headers.get("GameUrl", ""),
                "format": game_format,
                "pgn": pgn_string,
                "pgn_hash": pgn_hash,
                "source": source,
            }


def extract_games_from_pgn_string(pgn_string: str, source: str) -> list[dict]:
        """
        generic method to Parse a PGN string and extracts all games into the standardized dictionary format.
        This method is generic and can be used for PGNs from any source.
        """
        if not pgn_string:
            return []

        pgn_io = io.StringIO(pgn_string)
        extracted_games = []
        while True:
            try:
                # chess.pgn.read_game() can return None at EOF or skip headers/errors
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                pgn_string = str(game)
                pgn_hash = is_new_game(pgn_string)
                # hopefully this reduces the overhead expecially with the API calls and database creation of new players in pgn_dict
                if pgn_hash is False:
                    continue # skip this game if it's already in the database, we don't want to duplicate games
                extracted_games.append(pgn_to_dict(pgn_string, source, pgn_hash))
            except Exception as e:
                #print(f"Error reading a game from PGN: {e}")
                continue 
        return extracted_games