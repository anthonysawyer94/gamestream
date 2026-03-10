from datetime import datetime, timedelta

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q
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
    # 'fra_1': {'name': 'Soccer', 'league': 'Ligue 1', 'sport_path': 'soccer/fra.1', 'color': '#091C3E'},
    'usa_1': {'name': 'Soccer', 'league': 'MLS', 'sport_path': 'soccer/usa.1', 'color': '#335222'},
    'uefa_champions': {'name': 'Soccer', 'league': 'Champions League', 'sport_path': 'soccer/uefa.champions', 'color': '#0E1F3C'},
    'uefa_europa': {'name': 'Soccer', 'league': 'Europa League', 'sport_path': 'soccer/uefa.europa', 'color': '#FF6600'},
    'fifa_world': {'name': 'Soccer', 'league': 'World Cup', 'sport_path': 'soccer/fifa.world', 'color': '#1B1B1B'},
    'ufc': {'name': 'MMA', 'league': 'UFC', 'sport_path': 'mma/ufc', 'color': '#D00000'},
    'f1': {'name': 'Racing', 'league': 'F1', 'sport_path': 'racing/f1', 'color': '#FF1801'},

    # 'tennis_wta': {'name': 'Tennis', 'league': 'WTA', 'sport_path': 'tennis/wta', 'color': '#FF69B4'},
    # 'tennis_atp': {'name': 'Tennis', 'league': 'ATP', 'sport_path': 'tennis/atp', 'color': '#4169E1'},
}

BROADCAST_MAPPING = {
    'ESPN': ['espn_plus'],
    'ESPN2': ['espn_plus'],
    'ESPN+': ['espn_plus'],
    'ABC': ['fubotv', 'youtube_tv'],
    'TNT': ['youtube_tv', 'fubotv'],
    'TBS': ['fubotv', 'youtube_tv'],
    'NBA TV': None,
    'MLB Network': None,
    'FOX': ['fubotv', 'youtube_tv'],
    'FS1': ['fubotv', 'youtube_tv'],
    'Amazon': ['prime_video'],
    'Prime Video': ['prime_video'],
    'Netflix': ['netflix'],
    'HBO Max': ['hbo_max'],
    'Max': ['hbo_max'],
    'Paramount+': ['paramount_plus'],
    'Apple TV': ['apple_tv'],
    'Peacock': ['peacock'],
    'NBC': None,
    'USA': ['fubotv', 'youtube_tv'],
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
            self.fetch_sport_schedule(
                sport_data['sport_path'], sport_key, days)

        cutoff = timezone.now() - timedelta(days=2)
        deleted_count = Game.objects.filter(
            Q(start_time__lt=cutoff) | Q(start_time__isnull=True, status__in=['post', 'canceled'])
        ).delete()[0]
        if deleted_count:
            self.stdout.write(self.style.WARNING(
                f"Deleted {deleted_count} games older than 2 days"))

        self.stdout.write(self.style.SUCCESS(
            'Successfully fetched sports schedule'))

    def fetch_sport_schedule(self, sport_path, sport_key, days):
        # Check if this is a UFC/MMA sport - handle differently (individual athletes, not teams)
        if sport_path.startswith('mma/'):
            self.fetch_ufc_schedule(sport_path, sport_key, days)
            return

        # Check if this is F1 racing - handle differently (filter Qual and Race only)
        if sport_path.startswith('racing/'):
            self.fetch_f1_schedule(sport_path, sport_key, days)
            return

        # Fetch more days for World Cup (tournament is in June 2026)
        if sport_key == 'fifa_world':
            days = 120  # Fetch ~4 months ahead for World Cup

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
        # Start from yesterday to cover timezone overlap
        start_date = today - timedelta(days=1)
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
                self.stdout.write(self.style.WARNING(
                    f"Error fetching {date_str}: {e}"))
                continue

    def process_events(self, events, sport):
        tbd_team = self.get_tbd_team(sport)

        for event in events:
            try:
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                home_team_data = next(
                    (c for c in competitors if c.get('homeAway') == 'home'), None)
                away_team_data = next(
                    (c for c in competitors if c.get('homeAway') == 'away'), None)

                teams_tbd = False
                if not home_team_data or not away_team_data:
                    teams_tbd = True
                    home_team = tbd_team
                    away_team = tbd_team
                else:
                    home_team = self.get_or_create_team(home_team_data, sport)
                    away_team = self.get_or_create_team(away_team_data, sport)

                start_time_str = competition.get('date')
                if start_time_str:
                    start_time = datetime.fromisoformat(
                        start_time_str.replace('Z', '+00:00'))
                    time_tbd = False
                else:
                    start_time = None
                    time_tbd = True

                if time_tbd and teams_tbd:
                    tbd_status = 'both'
                elif time_tbd:
                    tbd_status = 'time'
                elif teams_tbd:
                    tbd_status = 'teams'
                else:
                    tbd_status = ''

                broadcast_names = competition.get('broadcasts', [{}])[0].get(
                    'names', []) if competition.get('broadcasts') else []
                broadcast = broadcast_names[0] if broadcast_names else ''

                streaming_services = []
                if broadcast_names:
                    for b in broadcast_names:
                        for key, slug in BROADCAST_MAPPING.items():
                            if key and key.lower() in b.lower():
                                slugs = slug if slug and isinstance(
                                    slug, list) else [slug]
                                for s in slugs:
                                    if s:
                                        service = StreamingService.objects.filter(
                                            slug=s).first()
                                        if service and service not in streaming_services:
                                            streaming_services.append(service)

                if not streaming_services:
                    continue

                status = competition.get('status', {}).get(
                    'type', {}).get('state', 'scheduled')

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
                home_rank = None
                away_rank = None
                if home_team_data:
                    home_rank = home_team_data.get(
                        'curatedRank', {}).get('current')
                if away_team_data:
                    away_rank = away_team_data.get(
                        'curatedRank', {}).get('current')
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
                            'status': status,
                            'round_name': round_name,
                            'leg': leg,
                            'total_legs': total_legs,
                            'home_rank': home_rank,
                            'away_rank': away_rank,
                            'tbd_status': tbd_status,
                        }
                    )
                    if streaming_services:
                        game.streaming_services.set(streaming_services)

            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Error processing event: {e}"))
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

        # Extract record from team_data - take first record with summary
        record = ''
        records = team_data.get('records', [])
        for rec in records:
            if rec.get('summary'):
                record = rec.get('summary', '')
                break

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
            # Always update record from API
            if record:
                team.record = record
                updated = True
            if updated:
                team.save()
        return team

    def get_tbd_team(self, sport):
        team, created = Team.objects.get_or_create(
            sport=sport,
            espn_id='tbd',
            defaults={
                'name': 'TBD',
                'abbreviation': 'TBD',
                'logo_url': '',
            }
        )
        return team

    def fetch_ufc_schedule(self, sport_path, sport_key, days):
        """Fetch UFC/MMA fights - they use individual athletes instead of teams"""
        sport, created = Sport.objects.get_or_create(
            slug=sport_key,
            defaults={
                'name': SPORT_MAPPING[sport_key]['name'],
                'league': SPORT_MAPPING[sport_key]['league'],
                'color': SPORT_MAPPING[sport_key].get('color', ''),
            }
        )

        today = timezone.now().date()
        start_date = today - timedelta(days=1)

        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            date_str = date.strftime('%Y%m%d')

            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'events' in data:
                    self.process_ufc_events(data['events'], sport)

            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(
                    f"Error fetching UFC {date_str}: {e}"))
                continue

    def process_ufc_events(self, events, sport):
        """Process UFC fights - uses athletes instead of teams"""
        for event in events:
            event_name = event.get('name', 'UFC Fight')
            event_id = event.get('id')

            competitions = event.get('competitions', [])

            for competition in competitions:
                try:
                    competitors = competition.get('competitors', [])

                    if len(competitors) < 2:
                        continue

                    competition_id = competition.get('id')

                    competition_type = competition.get('type', {})
                    weight_class = competition_type.get('abbreviation', '')

                    status = competition.get('status', {})
                    status_state = status.get('state', 'pre')

                    fighter1_data = competitors[0]
                    fighter2_data = competitors[1]

                    fighter1 = fighter1_data.get('athlete', {})
                    fighter2 = fighter2_data.get('athlete', {})

                    fighter1_name = fighter1.get('displayName', 'Unknown')
                    fighter2_name = fighter2.get('displayName', 'Unknown')

                    fighter1_record = ''
                    fighter2_record = ''

                    f1_records = fighter1_data.get('records', [])
                    if f1_records:
                        fighter1_record = f1_records[0].get('summary', '')

                    f2_records = fighter2_data.get('records', [])
                    if f2_records:
                        fighter2_record = f2_records[0].get('summary', '')

                    fighter1_athlete_id = fighter1_data.get('id')
                    fighter2_athlete_id = fighter2_data.get('id')

                    fighter1_details = self.fetch_fighter_details(
                        fighter1_athlete_id)
                    fighter2_details = self.fetch_fighter_details(
                        fighter2_athlete_id)

                    unique_fighter_id = f"ufc_{event_id}_{competition_id}"

                    fighter1_team, _ = Team.objects.get_or_create(
                        sport=sport,
                        espn_id=f"{unique_fighter_id}_f1",
                        defaults={
                            'name': fighter1_name,
                            'abbreviation': fighter1_name[:10].upper().replace(' ', ''),
                            'logo_url': '',
                            'record': fighter1_record,
                            'headshot_url': fighter1_details.get('headshot_url', ''),
                            'height': fighter1_details.get('height', ''),
                            'weight': fighter1_details.get('weight', ''),
                            'reach': fighter1_details.get('reach', ''),
                            'stance': fighter1_details.get('stance', ''),
                            'nickname': fighter1_details.get('nickname', ''),
                            'age': fighter1_details.get('age'),
                        }
                    )

                    fighter2_team, _ = Team.objects.get_or_create(
                        sport=sport,
                        espn_id=f"{unique_fighter_id}_f2",
                        defaults={
                            'name': fighter2_name,
                            'abbreviation': fighter2_name[:10].upper().replace(' ', ''),
                            'logo_url': '',
                            'record': fighter2_record,
                            'headshot_url': fighter2_details.get('headshot_url', ''),
                            'height': fighter2_details.get('height', ''),
                            'weight': fighter2_details.get('weight', ''),
                            'reach': fighter2_details.get('reach', ''),
                            'stance': fighter2_details.get('stance', ''),
                            'nickname': fighter2_details.get('nickname', ''),
                            'age': fighter2_details.get('age'),
                        }
                    )

                    self.update_fighter_team(
                        fighter1_team, fighter1_details, fighter1_record)
                    self.update_fighter_team(
                        fighter2_team, fighter2_details, fighter2_record)

                    broadcast_names = []
                    geo_broadcasts = competition.get('geoBroadcasts', [])
                    for gb in geo_broadcasts:
                        media = gb.get('media', {})
                        short_name = media.get('shortName', '')
                        if short_name:
                            broadcast_names.append(short_name)

                    streaming_services = []
                    for b in broadcast_names:
                        for key, slug in BROADCAST_MAPPING.items():
                            if key and key.lower() in b.lower():
                                slugs = slug if slug and isinstance(
                                    slug, list) else [slug]
                                for s in slugs:
                                    if s:
                                        service = StreamingService.objects.filter(
                                            slug=s).first()
                                        if service and service not in streaming_services:
                                            streaming_services.append(service)

                    if not streaming_services:
                        continue

                    start_time_str = competition.get('date')
                    if start_time_str:
                        start_time = datetime.fromisoformat(
                            start_time_str.replace('Z', '+00:00'))
                        time_tbd = False
                    else:
                        start_time = None
                        time_tbd = True

                    # Determine card type based on format (5 rounds = main event)
                    card_type = ''
                    format_data = competition.get('format', {})
                    periods = format_data.get(
                        'regulation', {}).get('periods', 3)
                    if periods == 5:
                        card_type = 'main_card'
                    else:
                        continue  # Skip non-main-card fights

                    round_label = f"{event_name}"
                    if weight_class:
                        round_label = f"{weight_class}: {fighter1_name} vs {fighter2_name}"

                    tbd_status = 'time' if time_tbd else ''

                    game, created = Game.objects.update_or_create(
                        sport=sport,
                        espn_id=f"{event_id}-{competition_id}",
                        defaults={
                            'home_team': fighter1_team,
                            'away_team': fighter2_team,
                            'start_time': start_time,
                            'broadcast': ', '.join(broadcast_names) if broadcast_names else '',
                            'status': status_state,
                            'round_name': round_label,
                            'card_type': card_type,
                            'tbd_status': tbd_status,
                        }
                    )
                    if streaming_services:
                        game.streaming_services.set(streaming_services)

                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"Error processing UFC fight: {e}"))
                    continue

    def fetch_fighter_details(self, athlete_id):
        """Fetch additional fighter details from ESPN athlete API"""
        if not athlete_id:
            return {}

        try:
            url = f"https://sports.core.api.espn.com/v2/sports/mma/athletes/{athlete_id}?lang=en&region=us"
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return {}

            athlete = response.json()

            return {
                'headshot_url': athlete.get('headshot', {}).get('href', ''),
                'height': athlete.get('displayHeight', ''),
                'weight': athlete.get('displayWeight', ''),
                'reach': athlete.get('displayReach', ''),
                'stance': athlete.get('stance', {}).get('text', '') if athlete.get('stance') else '',
                'nickname': athlete.get('nickname', ''),
                'age': athlete.get('age'),
            }
        except Exception:
            return {}

    def update_fighter_team(self, team, details, record):
        """Update existing fighter team with additional details"""
        updated = False

        if details.get('headshot_url') and not team.headshot_url:
            team.headshot_url = details.get('headshot_url', '')
            updated = True
        if details.get('height') and not team.height:
            team.height = details.get('height', '')
            updated = True
        if details.get('weight') and not team.weight:
            team.weight = details.get('weight', '')
            updated = True
        if details.get('reach') and not team.reach:
            team.reach = details.get('reach', '')
            updated = True
        if details.get('stance') and not team.stance:
            team.stance = details.get('stance', '')
            updated = True
        if details.get('nickname') and not team.nickname:
            team.nickname = details.get('nickname', '')
            updated = True
        if details.get('age') and not team.age:
            team.age = details.get('age')
            updated = True

        if updated:
            team.save()

    def fetch_f1_schedule(self, sport_path, sport_key, days):
        """Fetch F1 races - filter for Qualifying and Race only (no practice sessions)"""
        sport, created = Sport.objects.get_or_create(
            slug=sport_key,
            defaults={
                'name': SPORT_MAPPING[sport_key]['name'],
                'league': SPORT_MAPPING[sport_key]['league'],
                'color': SPORT_MAPPING[sport_key].get('color', ''),
            }
        )

        today = timezone.now().date()
        start_date = today - timedelta(days=1)

        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            date_str = date.strftime('%Y%m%d')

            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}"

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'events' in data:
                    self.process_f1_events(data['events'], sport)

            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(
                    f"Error fetching F1 {date_str}: {e}"))
                continue

    def process_f1_events(self, events, sport):
        """Process F1 events - filter for Qualifying and Race only"""
        # Get or create a placeholder team for F1 races
        f1_team, _ = Team.objects.get_or_create(
            sport=sport,
            espn_id='f1_race',
            defaults={
                'name': 'F1 Race',
                'abbreviation': 'F1',
                'logo_url': '',
            }
        )

        for event in events:
            try:
                event_name = event.get('name', 'F1 Grand Prix')
                event_id = event.get('id')

                # Get circuit location
                circuit = event.get('circuit', {})
                circuit_address = circuit.get('address', {})
                city = circuit_address.get('city', '')
                country = circuit_address.get('country', '')
                venue = f"{city}, {country}" if city and country else (
                    city or country or '')

                competitions = event.get('competitions', [])

                for competition in competitions:
                    competition_type = competition.get('type', {})
                    comp_id = competition_type.get('id', '')
                    comp_abbrev = competition_type.get('abbreviation', '')

                    # Only process Qualifying (id=2) and Race (id=3), skip FP1, FP2, FP3
                    if comp_id not in ['2', '3']:
                        continue

                    start_time_str = competition.get('date')
                    if start_time_str:
                        start_time = datetime.fromisoformat(
                            start_time_str.replace('Z', '+00:00'))
                        time_tbd = False
                    else:
                        start_time = None
                        time_tbd = True

                    broadcast_names = []
                    geo_broadcasts = competition.get('geoBroadcasts', [])
                    for gb in geo_broadcasts:
                        media = gb.get('media', {})
                        short_name = media.get('shortName', '')
                        if short_name:
                            broadcast_names.append(short_name)

                    # Also check regular broadcasts
                    broadcasts = competition.get('broadcasts', [])
                    for b in broadcasts:
                        names = b.get('names', [])
                        broadcast_names.extend(names)

                    # Also check broadcast field directly
                    direct_broadcast = competition.get('broadcast', '')
                    if direct_broadcast and direct_broadcast not in broadcast_names:
                        broadcast_names.append(direct_broadcast)

                    streaming_services = []
                    for b in broadcast_names:
                        for key, slug in BROADCAST_MAPPING.items():
                            if key and key.lower() in b.lower():
                                slugs = slug if slug and isinstance(
                                    slug, list) else [slug]
                                for s in slugs:
                                    if s:
                                        service = StreamingService.objects.filter(
                                            slug=s).first()
                                        if service and service not in streaming_services:
                                            streaming_services.append(service)

                    if not streaming_services:
                        continue

                    # Strip sponsor prefixes from event name
                    sponsors = ['Qatar Airways ', 'Heineken ', 'Crypto.com ', 'Lenovo ', 'Gulf Air ',
                                'STC ', 'MSC Cruises ', 'Pirelli ', 'Belgian ', 'AWS ',
                                'Tag Heuer ', 'Singapore Airlines ', 'Etihad Airways ']
                    clean_event_name = event_name
                    for sponsor in sponsors:
                        clean_event_name = clean_event_name.replace(
                            sponsor, '')

                    # Determine round label (Grand Prix name + type)
                    round_label = clean_event_name
                    if comp_id == '2':
                        round_label = f"{clean_event_name} - Qualifying"
                    else:
                        round_label = f"{clean_event_name} - Race"

                    status = competition.get('status', {})
                    status_state = status.get('state', 'pre')

                    tbd_status = 'time' if time_tbd else ''

                    game, created = Game.objects.update_or_create(
                        sport=sport,
                        espn_id=f"{event_id}-{comp_id}",
                        defaults={
                            'home_team': f1_team,
                            'away_team': f1_team,
                            'start_time': start_time,
                            'broadcast': ', '.join(broadcast_names) if broadcast_names else '',
                            'status': status_state,
                            'round_name': round_label,
                            'venue': venue,
                            'tbd_status': tbd_status,
                        }
                    )
                    if streaming_services:
                        game.streaming_services.set(streaming_services)

            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Error processing F1 event: {e}"))
                continue
