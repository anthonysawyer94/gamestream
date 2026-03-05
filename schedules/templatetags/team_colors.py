from django import template

register = template.Library()

LEAGUE_COLORS = {
    'NBA': {'color': '#1D428A', 'alternate': '#C8102E'},
    'WNBA': '#E0303E',
    'MLB': '#BD3E34',
    'MLS': '#335222',
    'Premier League': '#3D195B',
    'La Liga': '#EE8704',
    'Bundesliga': '#D20515',
    'Serie A': '#024494',
    'Ligue 1': '#091C3E',
    'Champions League': '#0E1F3C',
    'NCAA': '#002D72',
    'NHL': '#154734',
}


@register.simple_tag
def get_team_colors(team):
    return {
        'color': team.color or team.sport.color or LEAGUE_COLORS.get(team.sport.league, {}).get('color', '#1a1d21'),
        'alternate': team.alternate_color or LEAGUE_COLORS.get(team.sport.league, {}).get('alternate', '#2d3238'),
    }


@register.simple_tag
def get_league_color(sport):
    return sport.color or LEAGUE_COLORS.get(sport.league, '#1a1d21')
