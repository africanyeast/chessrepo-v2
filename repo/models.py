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
    # white = models.CharField(max_length=255, blank=True, null=True)
    # black = models.CharField(max_length=255, blank=True, null=True)
    white = models.ForeignKey('Player', on_delete=models.SET_NULL, related_name='white_games', null=True, blank=True)
    black = models.ForeignKey('Player', on_delete=models.SET_NULL, related_name='black_games', null=True, blank=True)
    
    # keep chesscom usernames as backup / fallback
    white_username = models.CharField(max_length=255, blank=True, null=True)
    black_username = models.CharField(max_length=255, blank=True, null=True)
    
    result = models.CharField(max_length=10, blank=True, null=True)
    opening = models.CharField(max_length=255, blank=True, null=True)
    eco = models.CharField(max_length=10, blank=True, null=True)
    whiteelo = models.CharField(blank=True, null=True)
    blackelo = models.CharField(blank=True, null=True)
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
    # Blitz, Rapid, Bullet, etc.
    format = models.CharField(max_length=20, blank=True, null=True)

    # Variant - represents the game variant (e.g., Standard, Fischer Random Chess, etc.)
    variant = models.CharField(max_length=100, blank=True, null=True)

    link = models.URLField(max_length=500, blank=True, null=True, unique=False) 
    pgn = models.TextField()
    pgn_hash = models.CharField(max_length=64, unique=True, db_index=True)
    source = models.CharField(max_length=20, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.white or 'N/A'} vs {self.black or 'N/A'} - {self.date or 'Unknown Date'}"

    class Meta:
        ordering = ['-date', '-endtime']
        db_table = 'games'
        verbose_name = 'Game'
        verbose_name_plural = 'Games'
        indexes = [
            models.Index(fields=['date']),
            # models.Index(fields=['date', 'endtime']),
            # models.Index(fields=['white']),
            # models.Index(fields=['black']),
            # models.Index(fields=['tournament']),
            # models.Index(fields=['tournament', 'endtime']),
        ]


class Player(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    fide_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=10, blank=True, null=True)
    chesscom_username = models.CharField(max_length=100, unique=True, blank=True, null=True)
    lichess_username = models.CharField(max_length=100, unique=True, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or self.username
    
    class Meta:
        ordering = ['name']
        db_table = 'players'
        verbose_name = 'Player'
        verbose_name_plural = 'Players'