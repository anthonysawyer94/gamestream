from django.db import models

from services.models import StreamingService


class Sport(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    league = models.CharField(max_length=50)
    color = models.CharField(max_length=7, blank=True, default='')

    def __str__(self):
        return f"{self.league} - {self.name}"


class Team(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    logo_url = models.URLField(blank=True)
    color = models.CharField(max_length=7, blank=True, default='')
    alternate_color = models.CharField(max_length=7, blank=True, default='')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='teams')
    espn_id = models.CharField(max_length=20)
    record = models.CharField(max_length=15, blank=True, default='')

    class Meta:
        unique_together = ('sport', 'espn_id')

    def __str__(self):
        return f"{self.abbreviation} - {self.sport.league}"


class Game(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='games')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_games')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_games')
    start_time = models.DateTimeField()
    broadcast = models.CharField(max_length=200, blank=True)
    streaming_service = models.ForeignKey(
        StreamingService, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='games'
    )
    espn_id = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='scheduled')
    round_name = models.CharField(max_length=50, blank=True, default='')
    leg = models.PositiveIntegerField(null=True, blank=True)
    total_legs = models.PositiveIntegerField(null=True, blank=True)
    home_rank = models.PositiveIntegerField(null=True, blank=True)
    away_rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ('sport', 'espn_id')

    def __str__(self):
        return f"{self.away_team.abbreviation} @ {self.home_team.abbreviation} - {self.start_time.date()}"
