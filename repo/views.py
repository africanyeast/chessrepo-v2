from django.shortcuts import render
from .models import Game  # Assuming models.py is in the same app 'repo'
from datetime import date as py_date, timedelta
from collections import defaultdict
import time
from django.http import JsonResponse
from django.views.decorators.http import require_GET

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
    start = time.time()
    # Query with select_related to fetch related player data efficiently
    games_on_date = list(
    Game.objects.filter(date=target_date)
        .select_related('white', 'black')
        .values(
            'id', 'result', 'format', 'variant', 'tournament', 'source', 'endtime',
            'white__title', 'white__name', 'white_username',
            'black__title', 'black__name', 'black_username'
        )
        .order_by('tournament', 'endtime')
    )

    # Grouping phase
    grouped_games = defaultdict(list)

    for game in games_on_date:
        # Create a dictionary with game data including separate player fields
        game_data = {
            'id': game['id'],
            'white': {
                'title': game['white__title'],
                'name': game['white__name'],
            },
            'white_username': game['white_username'],
            'black': {
                'title': game['black__title'],
                'name': game['black__name'],
            },
            'black_username': game['black_username'],
            'result': game['result'],
            'format': game['format'],
            'variant': game['variant'],
            'tournament': game['tournament'],
            'endtime': game['endtime'],
        }
    
        group_key = (game['tournament'] or '').strip() or (game['source'] or '').strip() or "Uncategorized"
        grouped_games[group_key].append(game_data)
    
    # Convert to desired list-of-dicts format
    grouped_tournaments_list = [
        {"name": tournament_name, "games": tournament_games}
        for tournament_name, tournament_games in sorted(grouped_games.items())
    ]

    end = time.time()
    print(f"Total processing time: {end - start:.3f} seconds")
    
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
            'result': game.result,
            'opening': game.opening,
            'site': game.site,
            'tournament': game.tournament
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Game not found'
        }, status=404)

