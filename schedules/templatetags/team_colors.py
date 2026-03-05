from django import template

register = template.Library()

LEAGUE_COLORS = {
    'NBA': {'color': '#1D428A', 'alternate': '#C8102E'},
    'WNBA': {'color': '#E0303E', 'alternate': '#E0303E'},
    'MLB': {'color': '#BD3E34', 'alternate': '#FFFFFF'},
    'MLS': {'color': '#335222', 'alternate': '#FFFFFF'},
    'Premier League': {'color': '#3D195B', 'alternate': '#FFFFFF'},
    'La Liga': {'color': '#EE8704', 'alternate': '#FFFFFF'},
    'Bundesliga': {'color': '#D20515', 'alternate': '#FFFFFF'},
    'Serie A': {'color': '#024494', 'alternate': '#FFFFFF'},
    'Ligue 1': {'color': '#091C3E', 'alternate': '#FFFFFF'},
    'Champions League': {'color': '#0E1F3C', 'alternate': '#FFFFFF'},
    'NCAA': {'color': '#002D72', 'alternate': '#FFFFFF'},
    'NHL': {'color': '#154734', 'alternate': '#FFFFFF'},
}


@register.simple_tag
def get_team_colors(team):
    # Safety check: if team is a string, we can't get .color from it
    if isinstance(team, str) or not team:
        return {'color': '#1a1d21', 'alternate': '#2d3238'}

    # Get values safely using getattr in case fields are None/Null
    t_color = getattr(team, 'color', None)
    t_alt = getattr(team, 'alternate_color', None)

    # Safely get sport and league info
    sport = getattr(team, 'sport', None)
    sport_color = getattr(sport, 'color', None) if sport else None
    league_name = getattr(sport, 'league', '') if sport else ''
    
    # Ensure colors have # prefix (ESPN API returns without #)
    def ensure_hash(color):
        if color and not color.startswith('#'):
            return f'#{color}'
        return color
    
    # Get final colors with fallbacks
    final_color = ensure_hash(t_color) or ensure_hash(sport_color) or LEAGUE_COLORS.get(league_name, {}).get('color', '#1a1d21')
    final_alternate = ensure_hash(t_alt) or LEAGUE_COLORS.get(league_name, {}).get('alternate', '#2d3238')

    return {
        'color': final_color,
        'alternate': final_alternate,
    }


@register.simple_tag
def get_league_color(sport):
    if isinstance(sport, str) or not sport:
        return '#1a1d21'

    # Check if LEAGUE_COLORS entry is a dict or a string to prevent .get() errors
    league_data = LEAGUE_COLORS.get(getattr(sport, 'league', ''), '#1a1d21')

    if isinstance(league_data, dict):
        fallback = league_data.get('color', '#1a1d21')
    else:
        fallback = league_data

    return getattr(sport, 'color', None) or fallback


@register.filter
def get_weight_class(round_name):
    """Extract weight class from round_name (format: 'WeightClass: Fighter1 vs Fighter2')"""
    if not round_name:
        return ''
    # Get everything before the first colon
    if ':' in round_name:
        return round_name.split(':')[0].strip()
    return round_name
