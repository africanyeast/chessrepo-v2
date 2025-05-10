from django.db import models
import re
import datetime
from django.core.exceptions import ValidationError

# Custom DateField if it's not already defined elsewhere or if you want it specific to this app's models
class ChessDateField(models.DateField):
    """Custom DateField that accepts both YYYY-MM-DD and YYYY.MM.DD formats"""
    
    def to_python(self, value):
        if value is None or isinstance(value, datetime.date):
            return value
            
        if isinstance(value, str) and re.match(r'^\d{4}\.\d{2}\.\d{2}$', value):
            try:
                year, month, day = map(int, value.split('.'))
                return datetime.date(year, month, day)
            except (ValueError, TypeError):
                raise ValidationError(
                    f'"{value}" value has an invalid date format. It must be in YYYY-MM-DD or YYYY.MM.DD format.'
                )
        
        return super().to_python(value)

class Game(models.Model):
    white = models.CharField(max_length=255, blank=True, null=True)
    black = models.CharField(max_length=255, blank=True, null=True)
    result = models.CharField(max_length=10, blank=True, null=True)
    opening = models.CharField(max_length=255, blank=True, null=True)
    eco = models.CharField(max_length=10, blank=True, null=True)
    whiteelo = models.IntegerField(blank=True, null=True)
    blackelo = models.IntegerField(blank=True, null=True)
    event = models.CharField(max_length=255, blank=True, null=True)
    site = models.CharField(max_length=255, blank=True, null=True)
    tournament = models.CharField(max_length=255, blank=True, null=True)

    # PGN "Round" - represents the round number in the tournament
    round = models.CharField(max_length=100, blank=True, null=True)
    
    # PGN "Date" - represents the start date of the game
    date = ChessDateField(blank=True, null=True) 
    
    # PGN "EndDate" - represents the end date of the game
    enddate = ChessDateField(blank=True, null=True)
    endtime = models.TimeField(blank=True, null=True)
    
    timecontrol = models.CharField(max_length=100, blank=True, null=True)

    # Variant - represents the game variant (e.g., Standard, Fischer Random Chess, etc.)
    variant = models.CharField(max_length=100, blank=True, null=True)

    link = models.URLField(max_length=500, blank=True, null=True, unique=False) 
    pgn = models.TextField()
    pgn_hash = models.CharField(max_length=64, unique=True, db_index=True)
    source = models.CharField(max_length=50, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.white or 'N/A'} vs {self.black or 'N/A'} - {self.date or 'Unknown Date'}"

    class Meta:
        ordering = ['-date', '-id'] # Order by date descending, then by ID


# class Player(models.Model):
#     full_name = models.CharField(max_length=255, blank=True, null=True)
#     fide_id = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="FIDE ID of the player")
#     country = models.CharField(max_length=100, blank=True, null=True, help_text="Player's country (e.g., FIDE federation)")
#     title = models.CharField(max_length=10, blank=True, null=True, help_text="Player's FIDE title (e.g., GM, IM, WGM)")
    
#     fide_standard_rating = models.IntegerField(blank=True, null=True)
#     fide_rapid_rating = models.IntegerField(blank=True, null=True)
#     fide_blitz_rating = models.IntegerField(blank=True, null=True)
    
#     chesscom_username = models.CharField(max_length=100, unique=True, blank=True, null=True)
#     lichess_username = models.CharField(max_length=100, unique=True, blank=True, null=True)

#     def __str__(self):
#         return self.full_name or self.chesscom_username or self.lichess_username or f"Player {self.id}"

#     class Meta:
#         ordering = ['full_name']