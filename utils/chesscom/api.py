import requests
import datetime
import chess # Ensure this is imported if type hints use it
import chess.pgn
import io
# import json # No longer needed in this file with the removal of archive list fetching

class CHESSCOM_API:
    BASE_URL = "https://api.chess.com/pub/player"
    HEADERS = {
        'User-Agent': 'Chessrepo/1.0 (akinxwumi@proton.me)'
    }

    def get_player_games_current_month_pgn(self, username: str) -> str | None:
        """
        Retrieves all games for a given player for the CURRENT calendar year and month 
        from Chess.com API.

        Args:
            username: The Chess.com username of the player.

        Returns:
            A string containing the games in PGN format, or None if an error occurs.
        """
        now = datetime.datetime.now()
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m") # Format MM (e.g., 01, 11)

        url = f"{self.BASE_URL}/{username}/games/{year_str}/{month_str}/pgn"
        
        print(f"Fetching games for {username} for {year_str}-{month_str} from {url}")
        
        try:
            response = requests.get(url, headers=self.HEADERS)
            response.raise_for_status() 
            return response.text
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                print(f"No games found for {username} for {year_str}-{month_str} (404 Not Found). URL: {url}")
            else:
                print(f"HTTP error occurred while fetching games for {username}: {http_err} - Status: {response.status_code}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred while requesting games for {username}: {req_err}")
        
        return None

