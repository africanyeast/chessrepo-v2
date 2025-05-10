import re
import chess
import chess.pgn
import hashlib
import io

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

def generate_pgn_hash(pgn_string: str) -> str:
        return hashlib.sha256(pgn_string.encode('utf-8')).hexdigest()

def pgn_to_dict(game: chess.pgn.Game, source: str) -> dict:
        """Converts a chess.pgn.Game object to a standardized dictionary."""
        headers = game.headers
        pgn_string = str(game)
        
        if source=="chesscom":
            if headers.get("Opening"):
                opening_name = headers.get("Opening", "")
            elif headers.get("ECOUrl"):
                opening_name = extract_opening_from_chesscom_ecourl(headers.get("ECOUrl"))
            else:
                opening_name = ""
            # now let's implement extracting tournament name from the tournament headers
            # an example: https://www.chess.com/tournament/live/late-titled-tuesday-blitz-may-06-2025-5632457
            # the tournament name is "Late-Titled Tuesday Blitz" but we have to remove the date, url, and id
            # But if tournament is not titled tuesday or freestyle friday, then we can just use whatever is passed in the headers directly
            tournament_name = ""
            if headers.get("Tournament"):
                tournament_name = headers.get("Tournament", "")
                # Extract just the tournament name from the URL if it's a chess.com URL
                if "chess.com/tournament" in tournament_name:
                    tournament_name = tournament_name.split("/")[-1]
                # Only apply regex for Titled Tuesday and Freestyle Friday tournaments
                if "titled-tuesday" in tournament_name.lower() or "freestyle-friday" in tournament_name.lower():
                    tournament_name = tournament_name.replace("-", " ")
                    # Remove date patterns (like may-06-2025 or 2025-05-06)
                    tournament_name = re.sub(r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[- ]\d{2}[- ]\d{4}', '', tournament_name, flags=re.IGNORECASE)
                    tournament_name = re.sub(r'\d{4}[- ]\d{2}[- ]\d{2}', '', tournament_name)
                    # Remove any remaining numbers (like the tournament ID)
                    tournament_name = re.sub(r'\d+', '', tournament_name)
                    # Clean up extra spaces and trim
                    tournament_name = re.sub(r'\s+', ' ', tournament_name).strip()

            
            return {
                "white": headers.get("White", ""),
                "black": headers.get("Black", ""),
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
                "pgn": pgn_string,
                "pgn_hash": generate_pgn_hash(pgn_string),
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

            return {
                "white": headers.get("White", ""),
                "black": headers.get("Black", ""),
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
                "pgn": pgn_string,
                "pgn_hash": generate_pgn_hash(pgn_string),
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
                extracted_games.append(pgn_to_dict(game, source))
            except Exception as e:
                #print(f"Error reading a game from PGN: {e}")
                continue 
        return extracted_games