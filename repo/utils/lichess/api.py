import requests

class LICHESS_API:
    def __init__(self):
        self.BASE_URL = "https://lichess.org/api"
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_broadcast_top(self) -> dict | None:
        url = f"{self.BASE_URL}/broadcast/top"
        response = requests.get(url, headers=self.HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def get_finished_rounds_from_top_broadcast(self, top_broadcast: dict) -> list:
        # store the ids of finished rounds that are tier 1 or higher and active broadcasts from the top broadcast page
        finished_round_ids = []
        active_broadcasts = top_broadcast.get('active', [])

        if not isinstance(active_broadcasts, list):
            return [] # Return empty list if 'active' is not a list or not found

        for broadcast_item in active_broadcasts:
            if not isinstance(broadcast_item, dict):
                continue

            tour_info = broadcast_item.get('tour')
            round_to_link_info = broadcast_item.get('roundToLink')

            if not isinstance(tour_info, dict) or not isinstance(round_to_link_info, dict):
                continue

            tour_tier = tour_info.get('tier')
            is_round_finished = round_to_link_info.get('finished', False)
            round_id = round_to_link_info.get('id')
            #only tier 3 and higher events for now
            if tour_tier >= 3 and is_round_finished and round_id:
                finished_round_ids.append(round_id)
                
        
        return finished_round_ids

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