from datetime import datetime, timedelta

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from schedules.models import Game, Sport, Team
from services.models import StreamingService

SPORT_MAPPING = {
    'nba': {'name': 'Basketball', 'league': 'NBA', 'sport_path': 'basketball/nba', 'color': '#1D428A'},
    'mlb': {'name': 'Baseball', 'league': 'MLB', 'sport_path': 'baseball/mlb', 'color': '#BD3E34'},
    'nhl': {'name': 'Hockey', 'league': 'NHL', 'sport_path': 'hockey/nhl', 'color': '#154734'},
    'ncaamb': {'name': 'Basketball', 'league': 'NCAA', 'sport_path': 'basketball/mens-college-basketball', 'color': '#002D72'},
    'eng_1': {'name': 'Soccer', 'league': 'Premier League', 'sport_path': 'soccer/eng.1', 'color': '#3D195B'},
    'esp_1': {'name': 'Soccer', 'league': 'La Liga', 'sport_path': 'soccer/esp.1', 'color': '#EE8704'},
    'ger_1': {'name': 'Soccer', 'league': 'Bundesliga', 'sport_path': 'soccer/ger.1', 'color': '#D20515'},
    'ita_1': {'name': 'Soccer', 'league': 'Serie A', 'sport_path': 'soccer/ita.1', 'color': '#024494'},
    'fra_1': {'name': 'Soccer', 'league': 'Ligue 1', 'sport_path': 'soccer/fra.1', 'color': '#091C3E'},
    'usa_1': {'name': 'Soccer', 'league': 'MLS', 'sport_path': 'soccer/usa.1', 'color': '#335222'},
    'uefa_champions': {'name': 'Soccer', 'league': 'Champions League', 'sport_path': 'soccer/uefa.champions', 'color': '#0E1F3C'},
    'uefa_europa': {'name': 'Soccer', 'league': 'Europa League', 'sport_path': 'soccer/uefa.europa', 'color': '#FF6600'},
    'uefa_conference': {'name': 'Soccer', 'league': 'Conference League', 'sport_path': 'soccer/uefa.conference', 'color': '#4B0082'},
}

BROADCAST_MAPPING = {
    'ESPN': 'espn_plus',
    'ESPN2': 'espn_plus',
    'ESPN+': 'espn_plus',
    'ABC': None,
    'TNT': None,
    'TBS': None,
    'NBA TV': None,
    'MLB Network': None,
    'FOX': None,
    'FS1': None,
    'Amazon': 'prime_video',
    'Prime Video': 'prime_video',
    'Netflix': 'netflix',
    'HBO Max': 'hbo_max',
    'Max': 'hbo_max',
    'Paramount+': 'paramount_plus',
    'Apple TV+': 'apple_tv',
    'Peacock': 'peacock',
    'NBC': None,
    'USA': None,
    'Telemundo': None,
    'Universo': None,
}


class Command(BaseCommand):
    help = 'Fetch sports schedule from ESPN API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=9,
            help='Number of days to fetch (default: 9 - includes yesterday for timezone coverage)'
        )

    def handle(self, *args, **options):
        days = options['days']

        for sport_key, sport_data in SPORT_MAPPING.items():
            self.stdout.write(f"Fetching {sport_data['league']} schedule...")
            self.fetch_sport_schedule(sport_data['sport_path'], sport_key, days)

        cutoff = timezone.now() - timedelta(days=2)
        deleted_count = Game.objects.filter(start_time__lt=cutoff).delete()[0]
        if deleted_count:
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} games older than 2 days"))

        self.stdout.write(self.style.SUCCESS('Successfully fetched sports schedule'))

    def fetch_sport_schedule(self, sport_path, sport_key, days):
        sport, created = Sport.objects.get_or_create(
            slug=sport_key,
            defaults={
                'name': SPORT_MAPPING[sport_key]['name'],
                'league': SPORT_MAPPING[sport_key]['league'],
                'color': SPORT_MAPPING[sport_key].get('color', ''),
            }
        )
        if not created and not sport.color:
            sport.color = SPORT_MAPPING[sport_key].get('color', '')
            sport.save()

        today = timezone.now().date()
        start_date = today - timedelta(days=1)  # Start from yesterday to cover timezone overlap
        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            date_str = date.strftime('%Y%m%d')

            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'events' in data:
                    self.process_events(data['events'], sport)

            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(f"Error fetching {date_str}: {e}"))
                continue

    def process_events(self, events, sport):
        for event in events:
            try:
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), None)

                if not home_team_data or not away_team_data:
                    continue

                home_team = self.get_or_create_team(home_team_data, sport)
                away_team = self.get_or_create_team(away_team_data, sport)

                start_time_str = competition.get('date')
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                else:
                    continue

                broadcast_names = competition.get('broadcasts', [{}])[0].get('names', []) if competition.get('broadcasts') else []
                broadcast = broadcast_names[0] if broadcast_names else ''

                streaming_service = None
                if broadcast_names:
                    for b in broadcast_names:
                        for key, slug in BROADCAST_MAPPING.items():
                            if key and key.lower() in b.lower():
                                streaming_service = StreamingService.objects.filter(slug=slug).first()
                                if streaming_service:
                                    broadcast = b
                                    break
                        if streaming_service:
                            break

                if not streaming_service:
                    continue

                status = competition.get('status', {}).get('type', {}).get('state', 'scheduled')

                round_name = ''
                leg = None
                total_legs = None
                series = competition.get('series', {})
                if series:
                    round_name = series.get('title', '')
                    total_legs = series.get('totalCompetitions')
                
                # Extract round info from notes (e.g., NCAA tournament rounds)
                if not round_name:
                    notes = competition.get('notes', [])
                    if notes:
                        note = notes[0].get('headline', '')
                        if note:
                            round_name = note
                
                leg_data = competition.get('leg', {})
                if leg_data:
                    leg = leg_data.get('value')

                # Extract team rankings
                home_rank = home_team_data.get('curatedRank', {}).get('current')
                away_rank = away_team_data.get('curatedRank', {}).get('current')
                # Only use ranking if it's a valid number (not 99 which means unranked)
                if home_rank and home_rank > 50:
                    home_rank = None
                if away_rank and away_rank > 50:
                    away_rank = None

                espn_event_id = event.get('id')
                if espn_event_id:
                    game, created = Game.objects.update_or_create(
                        sport=sport,
                        espn_id=espn_event_id,
                        defaults={
                            'home_team': home_team,
                            'away_team': away_team,
                            'start_time': start_time,
                            'broadcast': broadcast,
                            'streaming_service': streaming_service,
                            'status': status,
                            'round_name': round_name,
                            'leg': leg,
                            'total_legs': total_legs,
                            'home_rank': home_rank,
                            'away_rank': away_rank,
                        }
                    )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing event: {e}"))
                continue

    def get_or_create_team(self, team_data, sport):
        team_info = team_data.get('team', {})
        espn_id = team_info.get('id')

        if not espn_id:
            espn_id = team_data.get('id')

        team, created = Team.objects.get_or_create(
            sport=sport,
            espn_id=espn_id,
            defaults={
                'name': team_info.get('displayName', 'Unknown'),
                'abbreviation': team_info.get('abbreviation', 'UNK'),
                'logo_url': team_info.get('logo', ''),
                'color': team_info.get('color', ''),
                'alternate_color': team_info.get('alternateColor', ''),
            }
        )
        if not created:
            # Update missing data for existing teams
            updated = False
            if not team.logo_url and team_info.get('logo'):
                team.logo_url = team_info.get('logo', '')
                updated = True
            if not team.color and team_info.get('color'):
                team.color = team_info.get('color', '')
                updated = True
            if not team.alternate_color and team_info.get('alternateColor'):
                team.alternate_color = team_info.get('alternateColor', '')
                updated = True
            if updated:
                team.save()
        return team
