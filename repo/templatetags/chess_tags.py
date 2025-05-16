from django import template

register = template.Library()

def get_player_unique_key(player_obj, player_username_fallback, default_key_prefix):
    """Helper to get a unique key for a player (ID or username, with a fallback)."""
    if player_obj and player_obj.get('id'):
        return player_obj.get('id')
    if player_username_fallback:
        return player_username_fallback
    return default_key_prefix # Should be unique for P1 vs P2 if both are fully anonymous

@register.filter
def calculate_match_score(games):
    if not games:
        return {'player1': format_score_with_fraction(0), 'player2': format_score_with_fraction(0)}

    first_game = games[0]

    # Player 1 is defined as the one who played White in the first game of this match group.
    # Player 2 is defined as the one who played Black in the first game of this match group.
    # Their unique keys are determined for consistent tracking across all games in the match.
    
    player1_key_default = "ANONYMOUS_PLAYER_AS_WHITE_IN_FIRST_GAME"
    player2_key_default = "ANONYMOUS_PLAYER_AS_BLACK_IN_FIRST_GAME"

    player1_unique_key = get_player_unique_key(
        first_game.get('white'), 
        first_game.get('white_username'),
        player1_key_default
    )
    player2_unique_key = get_player_unique_key(
        first_game.get('black'),
        first_game.get('black_username'),
        player2_key_default
    )

    # Ensure player1_unique_key and player2_unique_key are distinct if both fall back to defaults
    # that might be identical (e.g. if both default_key_prefix were the same).
    # Given player1_key_default and player2_key_default are different, this is less of a concern here,
    # but good practice if defaults could collide.
    if player1_unique_key == player2_unique_key and player1_unique_key == player1_key_default : # Or any shared default
         # This specific scenario (P1 default == P2 default) is avoided by distinct default strings.
         # If they could be the same, one would need adjustment: e.g. player2_unique_key += "_alt"
         pass


    player1_total_score = 0.0  # Score for the player who was white in the first game (player1_unique_key)
    player2_total_score = 0.0  # Score for the player who was black in the first game (player2_unique_key)

    for game in games:
        current_white_key = get_player_unique_key(
            game.get('white'),
            game.get('white_username'),
            player1_key_default # Use P1's default if current white is anon (consistent with P1 if P1 was anon white)
        )
        current_black_key = get_player_unique_key(
            game.get('black'),
            game.get('black_username'),
            player2_key_default # Use P2's default if current black is anon (consistent with P2 if P2 was anon black)
        )
        
        # If current_white_key and current_black_key resolved to the same default anonymous key,
        # they need to be distinguished for this game's logic.
        if current_white_key == current_black_key and current_white_key == player1_key_default: # Example shared default
            # This implies both players in *this* game are anonymous.
            # We need to map them to player1_unique_key and player2_unique_key based on their roles.
            # The get_player_unique_key defaults are designed to align with P1/P2 roles if they were anonymous.
            # If P1 was anon white (key player1_key_default) and P2 was anon black (key player2_key_default),
            # then current_white_key will match player1_unique_key if current white is anon,
            # and current_black_key will match player2_unique_key if current black is anon.
            pass


        result = game.get('result')

        # Determine who won based on whether the current game's players match player1_unique_key or player2_unique_key
        if current_white_key == player1_unique_key and current_black_key == player2_unique_key:
            # Player 1 (as defined by first game) was White, Player 2 was Black
            if result == "1-0": player1_total_score += 1.0
            elif result == "0-1": player2_total_score += 1.0
            elif result == "1/2-1/2":
                player1_total_score += 0.5
                player2_total_score += 0.5
        elif current_white_key == player2_unique_key and current_black_key == player1_unique_key:
            # Player 2 (as defined by first game) was White, Player 1 was Black
            if result == "1-0": player2_total_score += 1.0
            elif result == "0-1": player1_total_score += 1.0
            elif result == "1/2-1/2":
                player1_total_score += 0.5
                player2_total_score += 0.5
        # else:
            # This case suggests the players in 'game' do not match the pair from 'first_game'.
            # This should ideally not happen if the 'games' list is correctly grouped by 'player_pair'.
            # print(f"DEBUG: Player mismatch in calculate_match_score. Game: {current_white_key} vs {current_black_key}. Expected pair: {player1_unique_key} vs {player2_unique_key}")
            
    return {
        'player1': format_score_with_fraction(player1_total_score),
        'player2': format_score_with_fraction(player2_total_score)
    }

def format_score_with_fraction(score):
    """Convert decimal scores to use fraction symbols (½ instead of .5)"""
    if score == int(score):  # Whole number
        return str(int(score))
    else:
        whole_part = int(score)
        # Fix for scores like 0.5 to display as "½" instead of "0½"
        if whole_part == 0 and score == 0.5:
            return "½"
        elif score - whole_part == 0.5:
            return f"{whole_part}½"  # Using the actual half symbol
        # For any other fractional values (unlikely in chess)
        return str(score)

@register.filter
def format_game_result(result):
    """Format game result to display draws as fractions"""
    if result == "1/2-1/2":
        return "½-½"
    return result