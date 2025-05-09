# fetch chess.com player data depending on max page and save to json file
import requests
from bs4 import BeautifulSoup
import json
import time
import re

class CHESSCOM_CRAWLER:

    BASE_URL = "https://www.chess.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    PLAYERS_LIST_URL = f"{BASE_URL}/players"
    MAX_PAGES = 8
    OUTPUT_FILE = "utils/chesscom_players.json"

    def get_soup(url):
        """Fetches a URL and returns a BeautifulSoup object."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_player_profile_url(player_page_url):
        """Extracts the /member/username URL from a player's detail page."""
        if not player_page_url.startswith('http'):
            player_page_url = BASE_URL + player_page_url

        soup = get_soup(player_page_url)
        if not soup:
            return None, None

        # Look for a link that contains "/member/" in its href
        # This is a common pattern, but might need adjustment if the structure is changed
        profile_link_tag = soup.find('a', href=re.compile(r'/member/'))
        
        if profile_link_tag and profile_link_tag.get('href'):
            profile_url = profile_link_tag['href']
            if not profile_url.startswith('http'):
                profile_url = BASE_URL + profile_url
            
            # Extract username from the profile URL
            match = re.search(r'/member/([^/?]+)', profile_url)
            username = match.group(1) if match else None
            return profile_url, username

        print(f"Could not find profile URL on {player_page_url}")
        return None, None


    def get_players_data():
        all_players_data = []

        for page_num in range(1, MAX_PAGES + 1):
            if page_num == 1:
                url = PLAYERS_LIST_URL
            else:
                url = f"{PLAYERS_LIST_URL}?page={page_num}"

            print(f"Scraping page: {url}")
            soup = get_soup(url)
            if not soup:
                time.sleep(2) # Wait before retrying or moving to next page
                continue

            # Find player entries. This selector needs to be accurate.
            # Based on the web search results, players are listed.
            # Common structure: <tr> for tables, or <div> for list items.
            # Let's assume a structure like <div class="player-row"> or similar.
            # We will look for elements that seem to contain player name, rating, and a link.
            
            # The search results show player items like:
            # GM Magnus Carlsen 2837 | #1 Norway
            # We need to find the container for each player.
            # Let's try to find `<a>` tags with `/players/` in href, then go to parent.
            
            player_links = soup.find_all('a', class_=re.compile(r'master-players-player-name|user-username-component', re.IGNORECASE), href=re.compile(r'/players/'))

            # if not player_links:
            #      # Fallback: Try a more generic approach if specific classes are not found
            #      # This looks for <tr> elements that seem to contain player data.
            #      player_containers = soup.find_all('tr', class_=re.compile(r'master-players-table-row', re.IGNORECASE))
            #      if not player_containers:
            #          print(f"No player containers found on page {page_num} with common selectors. Trying generic divs.")
            #          # A very generic attempt if specific table rows aren't found
            #          player_containers = soup.find_all('div', class_=re.compile(r'player-preview-component|list-item-component', re.IGNORECASE))


            processed_player_page_links = set()

            for player_link_tag in player_links:
                player_name = player_link_tag.get_text(strip=True)
                player_page_link = player_link_tag['href']

                if not player_page_link.startswith('http'):
                    player_page_link = BASE_URL + player_page_link
                
                if player_page_link in processed_player_page_links:
                    continue # Already processed this player (e.g. if name and username link separately)
                processed_player_page_links.add(player_page_link)

                # Find the parent element that contains rating and rank
                # This often requires inspecting the HTML structure.
                # Let's assume the rating/rank is near the player_name link.
                # We might need to go up a few parent levels.
                current_element = player_link_tag
                player_info_container = None
                for _ in range(4): # Try up to 4 parent elements
                    if current_element.parent:
                        current_element = current_element.parent
                        # Look for text matching "rating | #rank" pattern
                        text_content = current_element.get_text(separator=' ', strip=True)
                        # Regex to find rating and rank like "2837 | #1"
                        rating_rank_match = re.search(r'(\d{3,4})\s*\|\s*#(\d+)', text_content)
                        if rating_rank_match:
                            player_info_container = current_element
                            break
                    else:
                        break
                
                rating = None
                ranking = None

                if player_info_container:
                    text_content = player_info_container.get_text(separator=' ', strip=True)
                    rating_rank_match = re.search(r'(\d{3,4})\s*\|\s*#(\d+)', text_content)
                    if rating_rank_match:
                        rating = rating_rank_match.group(1)
                        ranking = rating_rank_match.group(2)
                    else:
                        # Fallback: try to find rating and rank in separate elements if not combined
                        rating_tag = player_info_container.find(class_=re.compile(r'master-players-rating', re.IGNORECASE))
                        rank_tag = player_info_container.find(class_=re.compile(r'master-players-rank', re.IGNORECASE))
                        if rating_tag: rating = rating_tag.get_text(strip=True)
                        if rank_tag: ranking = rank_tag.get_text(strip=True).replace('#','')
                
                if not rating or not ranking:
                    print(f"Could not find rating/rank for {player_name} on page {page_num}. Structure might have changed.")


                print(f"  Found player: {player_name}, Rating: {rating}, Rank: {ranking}, Page: {player_page_link}")

                # Now, go to the player's page to get their /member/ URL
                profile_url, username = None, None
                if player_page_link:
                    print(f"    Fetching profile URL from: {player_page_link}")
                    profile_url, username = extract_player_profile_url(player_page_link)
                    time.sleep(1) # Be respectful to the server

                player_data = {
                    "name": player_name,
                    "ranking": ranking,
                    "rating": rating,
                    "player_page_url": player_page_link,
                    "chesscom_profile_url": profile_url,
                    "chesscom_username": username
                }
                all_players_data.append(player_data)
                print(f"    Extracted: Username - {username}, Profile URL - {profile_url}")

            time.sleep(2) # Wait a bit before fetching the next page

        return all_players_data
    
    def save_to_json(data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def main():
        players_data = get_players_data()
        save_to_json(players_data, OUTPUT_FILE)
        print(f"\nData for {len(players_data)} players saved to {OUTPUT_FILE}")