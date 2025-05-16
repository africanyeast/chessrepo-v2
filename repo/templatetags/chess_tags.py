from django import template

register = template.Library()

@register.filter
def calculate_match_score(games):
    white_score = 0
    black_score = 0
    for game in games:
        if game['result'] == "1-0":
            white_score += 1
        elif game['result'] == "0-1":
            black_score += 1
        elif game['result'] == "1/2-1/2":
            white_score += 0.5
            black_score += 0.5
    
    # Convert decimal scores to fractions (e.g., 7.5 to 7½)
    white_display = format_score_with_fraction(white_score)
    black_display = format_score_with_fraction(black_score)
    
    # return f"{white_display}-{black_display}"
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