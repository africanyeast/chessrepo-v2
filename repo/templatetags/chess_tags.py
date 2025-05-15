from django import template

register = template.Library()

@register.filter
def calculate_match_score(games):
    white_score = 0
    black_score = 0
    
    # Debug: Print the games data to see what we're working with
    #print(f"Games data: {games}")
    
    for game in games:
        # Debug: Print each game to verify structure
        #print(f"Processing game: {game}")
        
        if 'result' not in game:
            print(f"Warning: Game missing 'result' key: {game}")
            continue
            
        if game['result'] == "1-0":
            white_score += 1
        elif game['result'] == "0-1":
            black_score += 1
        elif game['result'] == "1/2-1/2":
            white_score += 0.5
            black_score += 0.5
        else:
            print(f"Warning: Unexpected result value: {game['result']}")
    
    # Debug: Print final scores before formatting
    print(f"Final scores - White: {white_score}, Black: {black_score}")
    
    # Convert decimal scores to fractions (e.g., 7.5 to 7½)
    white_display = format_score_with_fraction(white_score)
    black_display = format_score_with_fraction(black_score)
    
    return {
        'white': white_display,
        'black': black_display
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