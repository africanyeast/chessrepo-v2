from django.shortcuts import render
from .models import Game  # Assuming models.py is in the same app 'repo'
from datetime import date as py_date, timedelta, datetime
from collections import defaultdict
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.http import require_GET

def get_title_weight(title):
    """
    Returns a numerical weight for player titles.
    Higher weights for stronger titles.
    """
    title_weights = {
        'GM': 100,
        'WGM': 90,
        'IM': 80,
        'WIM': 70,
        'FM': 60,
        'WFM': 50,
        'CM': 40,
        'WCM': 30,
        'NM': 20,
    }
    return title_weights.get(title, 0)

def calculate_tournament_strength(tournament_games):
    """
    Calculate the weighted average strength of a tournament based on player titles,
    with a penalty factor for tournaments with few games.
    Returns a score that can be used for sorting.
    """
    if not tournament_games:
        return 0
    
    total_weight = 0
    player_count = 0
    game_count = len(tournament_games)
    
    # Track unique players to avoid counting the same player multiple times
    seen_players = set()
    
    for game in tournament_games:
        # Process white player
        white_id = game['white']['id']
        white_title = game['white']['title']
        if white_id and white_id not in seen_players:
            total_weight += get_title_weight(white_title)
            seen_players.add(white_id)
            player_count += 1
            
        # Process black player
        black_id = game['black']['id']
        black_title = game['black']['title']
        if black_id and black_id not in seen_players:
            total_weight += get_title_weight(black_title)
            seen_players.add(black_id)
            player_count += 1
    
    # Calculate base strength (average weight per player)
    base_strength = total_weight / player_count if player_count > 0 else 0
    
    # Apply a scaling factor based on number of games
    # This will reduce the weight of tournaments with 1-2 games
    # Formula: final_strength = base_strength * (1 - e^(-games/2))

    scaling_factor = 1 - pow(2.718281828, -game_count / 2)    
    return base_strength * scaling_factor

def parse_url_date_param(date_str_from_url):
    """
    Parses a date string from URL parameter (MM/DD or MM/DD/YY)
    and returns a date object. Defaults to today if parsing fails or no string is provided.
    Example: "10/05" (current year) or "10/05/25" (for 2025-10-05).
    """
    if not date_str_from_url:
        return py_date.today()
    
    parts = date_str_from_url.split('/')
    current_year = py_date.today().year
    
    try:
        if len(parts) == 2: # Format: MM/DD
            month, day = int(parts[0]), int(parts[1])
            # Basic validation for month and day
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return py_date.today() # Fallback for invalid month/day
            return py_date(current_year, month, day)
        elif len(parts) == 3: # Format: MM/DD/YY
            month, day, year_short = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return py_date.today() # Fallback for invalid month/day
            
            # Convert YY to YYYY, assuming 20xx as per example "10/05/25" -> 2025
            year = 2000 + year_short if year_short < 100 else year_short
            return py_date(year, month, day)
        else: # Invalid format
            return py_date.today()
    except (ValueError, TypeError): # Handles non-integer parts or invalid date constructions
        return py_date.today()

def index(request):
    base_url = f"{request.scheme}://{request.get_host()}"
    date_param = request.GET.get('date')
    target_date = parse_url_date_param(date_param)
    # Fetch games for the target date.
    # The initial order_by helps in ensuring that when Python's stable sort is used later,
    # games within the same effective tournament group maintain their endtime order.
    # Fetch only necessary fields for games on the target date.
    # Query with select_related to fetch related player data efficiently
    games_on_date = list(
    Game.objects.filter(date=target_date)
        .select_related('white', 'black')
        .values(
            'id', 'result', 'tournament', 'endtime',
            'white__id', 'white__title', 'white__name', 'white_username', 'whiteelo',
            'black__id', 'black__title', 'black__name', 'black_username', 'blackelo'
        )
        .order_by('endtime')
    )

    # First, group games by player pairs
    player_pair_groups = defaultdict(list)
    
    for game in games_on_date:
        # Create a dictionary with game data including separate player fields
        white_id = game['white__id']
        black_id = game['black__id']
        white_name = (game['white__name'] or game['white_username'] or '').lower().strip()
        black_name = (game['black__name'] or game['black_username'] or '').lower().strip()
        
        # Create a normalized player pair identifier using player IDs when available
        tournament = game['tournament'] or ''
        if white_id and black_id:
            player_ids = sorted([white_id, black_id])
            player_pair = f"id-{tournament}-{player_ids[0]}-{player_ids[1]}"
        else:
            players = sorted([white_name, black_name])
            player_pair = f"name-{tournament}-{players[0]}-{players[1]}"
        
        # Calculate total rating for sorting
        white_elo = game.get('whiteelo') or 0
        black_elo = game.get('blackelo') or 0
        total_rating = int(white_elo) + int(black_elo)
        
        game_data = {
            'id': game['id'],
            'white': {
                'title': game['white__title'],
                'name': game['white__name'],
                'id': white_id,
            },
            'white_username': game['white_username'],
            'black': {
                'title': game['black__title'],
                'name': game['black__name'],
                'id': black_id,
            },
            'black_username': game['black_username'],
            'result': game['result'],
            'tournament': game['tournament'],
            'endtime': game['endtime'],
            'player_pair': player_pair,
            'total_rating': total_rating,
        }
        
        player_pair_groups[player_pair].append(game_data)
    
    # Now group by tournament, but keep player pairs together
    grouped_games = defaultdict(list)
    
    for player_pair, games in player_pair_groups.items():
        # Use the tournament from the first game in the group
        # This ensures all games between the same players go to the same tournament group
        if games:
            group_key = (games[0]['tournament'] or '').strip() or (games[0].get('source') or '').strip() or "Uncategorized"
            # Add all games from this player pair to the tournament group
            grouped_games[group_key].extend(games)
    
    # Convert to desired list-of-dicts format, but now sort player groups by number of games
    grouped_tournaments_list = []
    for tournament_name, tournament_games in sorted(grouped_games.items()):
        # Sort games by total rating in descending order
        sorted_games = sorted(tournament_games, key=lambda x: x.get('total_rating', 0), reverse=True)
        
        grouped_tournaments_list.append({
            "name": tournament_name,
            "games": sorted_games,
            "strength": calculate_tournament_strength(sorted_games)  # Calculate tournament strength
        })
    
    # Sort tournaments by strength in descending order
    grouped_tournaments_list.sort(key=lambda x: x['strength'], reverse=True)
    
    # Remove the strength field as it's no longer needed for the template
    for tournament in grouped_tournaments_list:
        del tournament['strength']
    
    # For date navigation links in the template
    prev_date_obj = target_date - timedelta(days=1)
    next_date_obj = target_date + timedelta(days=1)

    # Format date strings for URL parameters (e.g., "10/05/25")
    prev_date_url_param = prev_date_obj.strftime('%m/%d/%y').lower()
    next_date_url_param = next_date_obj.strftime('%m/%d/%y').lower()

    context = {
        'base_url': base_url,
        'grouped_tournaments': grouped_tournaments_list,
        'current_view_date': target_date,  # For displaying the current date
        'prev_date_url_param': prev_date_url_param,
        'next_date_url_param': next_date_url_param,
    }
    return render(request, 'index.html', context)

@require_GET
def get_game_pgn(request, game_id):
    """API endpoint to fetch a game's PGN data and metadata asynchronously"""
    try:
        # Get the game with related white and black player objects
        game = Game.objects.select_related('white', 'black').get(id=game_id)
        
        return JsonResponse({
            'success': True,
            'pgn': game.pgn,
            'white_title': game.white.title if game.white else None,
            'white_name': game.white.name if game.white else None,
            'white_username': game.white_username,
            'black_title': game.black.title if game.black else None,
            'black_name': game.black.name if game.black else None,
            'black_username': game.black_username,
            'whiteelo': game.whiteelo,
            'blackelo': game.blackelo,
            'result': game.result,
            'format': game.format,
            'opening': game.opening,
            'site': game.site,
            'tournament': game.tournament
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Game not found'
        }, status=404)


def download_pgn(request):
    """
    View to download all games for a specific date as a PGN file.
    Only fetches the PGN field which already contains complete game information.
    """
    # Get the date from the request query parameters
    date_str = request.GET.get('date')
    
    try:
        # Parse the date string into a datetime object
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            # If no date provided, use today's date
            date_obj = datetime.now().date()
            
        # Format the date for display in the filename
        formatted_date = date_obj.strftime('%Y-%m-%d')
        
        # Query only the PGN field for all games on the specified date
        games = Game.objects.filter(date=date_obj).values_list('pgn', flat=True)
        
        # Combine all PGNs into a single string
        pgn_content = "\n\n".join(pgn for pgn in games if pgn)
        
        # Create the response with the PGN content
        response = HttpResponse(pgn_content, content_type='application/x-chess-pgn')
        response['Content-Disposition'] = f'attachment; filename="chess_games_{formatted_date}.pgn"'
        
        return response
        
    except Exception as e:
        # Handle any errors
        return HttpResponse(f"Error generating PGN file: {str(e)}", status=500)

