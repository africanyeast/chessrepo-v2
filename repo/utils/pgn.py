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
        
        if headers.get("Opening"):
            opening_name = headers.get("Opening", "")
        elif source=="chesscom" and headers.get("ECOUrl"):
            opening_name = extract_opening_from_chesscom_ecourl(headers.get("ECOUrl"))
        else:
            opening_name = ""

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
            "tournament": headers.get("Tournament", ""),
            "date": headers.get("Date", ""),
            "enddate": headers.get("EndDate", headers.get("Date", "")),
            "endtime": headers.get("EndTime", ""),
            "timecontrol": headers.get("TimeControl", ""),
            "link": headers.get("Link", ""),
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