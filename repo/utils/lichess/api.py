import requests
import json

class LICHESS_API:
    def __init__(self):
        self.BASE_URL = "https://lichess.org/api"
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    # def get_broadcast_top(self) -> dict | None:
    #     url = f"{self.BASE_URL}/broadcast/top"
    #     response = requests.get(url, headers=self.HEADERS)
    #     if response.status_code == 200:
    #         return response.json()
    #     else:
    #         return None
    
    # def get_finished_rounds_from_top_broadcast(self, top_broadcast: dict) -> list:
    #     # store the ids of finished rounds that are tier 1 or higher and active broadcasts from the top broadcast page
    #     finished_round_ids = []
    #     active_broadcasts = top_broadcast.get('active', [])

    #     if not isinstance(active_broadcasts, list):
    #         return [] # Return empty list if 'active' is not a list or not found

    #     for broadcast_item in active_broadcasts:
    #         if not isinstance(broadcast_item, dict):
    #             continue

    #         tour_info = broadcast_item.get('tour')
    #         round_to_link_info = broadcast_item.get('roundToLink')

    #         if not isinstance(tour_info, dict) or not isinstance(round_to_link_info, dict):
    #             continue

    #         tour_tier = tour_info.get('tier')
    #         is_round_finished = round_to_link_info.get('finished', False)
    #         round_id = round_to_link_info.get('id')
    #         #only tier 1 and higher events for now
    #         if tour_tier >= 1 and is_round_finished and round_id:
    #             finished_round_ids.append(round_id)
                
        
    #     return finished_round_ids

    def get_finished_rounds_from_broadcast(self) -> dict:
        """
        Fetches all tournaments and their finished rounds from the broadcast endpoint.
        Returns a dictionary with tournament names as keys and lists of finished round IDs as values.
        """
        url = f"{self.BASE_URL}/broadcast"
        result = {}
        
        with requests.get(url, headers=self.HEADERS, stream=True) as response:
            if response.status_code != 200:
                return result
                
            # Process the NDJSON stream
            buffer = ""
            for chunk in response.iter_lines(decode_unicode=True):
                if chunk:
                    try:
                        broadcast_data = json.loads(chunk)
                        tour_name = broadcast_data.get('tour', {}).get('name')
                        
                        if tour_name:
                            # Get all finished rounds for this tournament
                            finished_rounds = [
                                round_data.get('id')
                                for round_data in broadcast_data.get('rounds', [])
                                if round_data.get('finished', False)
                            ]
                            
                            if finished_rounds:  # Only add tournaments with finished rounds
                                result[tour_name] = finished_rounds
                                    
                    except json.JSONDecodeError:
                        pass  # Skip invalid JSON
        
        return result

    def get_round_pgn(self, round_id: str) -> str | None:
        url = f"{self.BASE_URL}/broadcast/round/{round_id}.pgn"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def get_player_fide_profile(self, fide_id: str) -> dict | None:
        url = f"{self.BASE_URL}/fide/player/{fide_id}"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            return None