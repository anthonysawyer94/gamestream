from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from services.models import (StreamingService, UserSportPreference,
                             UserSubscription)

from .models import Game, Sport


def home(request):
    from datetime import timedelta
    
    today = timezone.localtime(timezone.now()).date()
    week_later = today + timedelta(days=7)

    games = Game.objects.filter(
        start_time__gte=timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time())),
        start_time__lt=timezone.make_aware(timezone.datetime.combine(week_later, timezone.datetime.min.time()))
    ).select_related('home_team', 'away_team', 'sport', 'streaming_service').order_by('start_time')

    cutoff_time = timezone.now() - timedelta(hours=5)
    games = games.exclude(
        status='post',
        start_time__lt=cutoff_time
    )

    user_services = []
    if request.user.is_authenticated:
        user_services = list(
            request.user.subscriptions.values_list('streaming_service_id', flat=True)
        )
        games = games.filter(
            Q(streaming_service_id__in=user_services) | 
            Q(streaming_service__isnull=True)
        )

    sports = Sport.objects.all()
    services = StreamingService.objects.all()

    games_by_date = {}
    for game in games:
        local_time = timezone.localtime(game.start_time)
        date_key = local_time.date()
        if date_key not in games_by_date:
            games_by_date[date_key] = []
        games_by_date[date_key].append(game)

    context = {
        'games_by_date': games_by_date,
        'sports': sports,
        'services': services,
        'user_services': user_services,
        'today': timezone.localtime(timezone.now()).date(),
    }
    return render(request, 'home.html', context)


def schedule(request):
    today = timezone.localtime(timezone.now()).date()
    week_later = today + timedelta(days=7)

    sport_id = request.GET.get('sport')
    filter_type = request.GET.get('filter_type', 'all')
    service_id = request.GET.get('service')

    games = Game.objects.filter(
        start_time__gte=timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time())),
        start_time__lt=timezone.make_aware(timezone.datetime.combine(week_later, timezone.datetime.min.time()))
    ).select_related('home_team', 'away_team', 'sport', 'streaming_service').order_by('start_time')

    cutoff_time = timezone.now() - timedelta(hours=5)
    games = games.exclude(
        status='post',
        start_time__lt=cutoff_time
    )

    if sport_id:
        games = games.filter(sport_id=sport_id)

    user_services = []
    user_sports = []
    if request.user.is_authenticated:
        user_services = list(
            request.user.subscriptions.values_list('streaming_service_id', flat=True)
        )
        user_sports = list(
            request.user.sport_preferences.values_list('sport_id', flat=True)
        )

    if filter_type == 'my_selected' and user_services:
        games = games.filter(streaming_service_id__in=user_services)
    elif filter_type == 'my_sports' and user_sports:
        games = games.filter(sport_id__in=user_sports)
    elif filter_type == 'all_streaming':
        games = games.exclude(streaming_service__isnull=True)
    elif filter_type == 'service' and service_id:
        games = games.filter(streaming_service_id=service_id)

    sports = Sport.objects.all()
    services = StreamingService.objects.all()

    games_by_date = {}
    for game in games:
        local_time = timezone.localtime(game.start_time)
        date_key = local_time.date()
        if date_key not in games_by_date:
            games_by_date[date_key] = []
        games_by_date[date_key].append(game)

    context = {
        'games_by_date': games_by_date,
        'sports': sports,
        'services': services,
        'selected_sport': sport_id,
        'selected_service': service_id,
        'filter_type': filter_type,
        'user_services': user_services,
        'user_sports': user_sports,
        'today': timezone.localtime(timezone.now()).date(),
    }
    return render(request, 'schedule.html', context)
