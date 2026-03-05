from django.contrib import admin

from .models import Game, Sport, Team


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'league', 'slug')
    search_fields = ('name', 'league')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'sport', 'espn_id')
    list_filter = ('sport',)
    search_fields = ('name', 'abbreviation')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'sport', 'start_time', 'streaming_service', 'status')
    list_filter = ('sport', 'streaming_service', 'status')
    search_fields = ('home_team__name', 'away_team__name')
    readonly_fields = ('espn_id',)
