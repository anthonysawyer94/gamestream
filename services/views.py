from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from schedules.models import Sport

from .models import StreamingService, UserSportPreference, UserSubscription


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def subscriptions(request):
    all_services = StreamingService.objects.all()
    all_sports = Sport.objects.all()
    user_subs = UserSubscription.objects.filter(user=request.user)
    user_sport_prefs = UserSportPreference.objects.filter(user=request.user)
    user_service_ids = set(user_subs.values_list('streaming_service_id', flat=True))
    user_sport_ids = set(user_sport_prefs.values_list('sport_id', flat=True))

    context = {
        'services': all_services,
        'sports': all_sports,
        'user_service_ids': user_service_ids,
        'user_sport_ids': user_sport_ids,
    }
    return render(request, 'subscriptions.html', context)


@login_required
def update_subscriptions(request):
    if request.method == 'POST':
        selected_service_ids = request.POST.getlist('services')
        selected_sport_ids = request.POST.getlist('sports')

        UserSubscription.objects.filter(user=request.user).delete()
        for service_id in selected_service_ids:
            UserSubscription.objects.get_or_create(
                user=request.user,
                streaming_service_id=service_id
            )

        UserSportPreference.objects.filter(user=request.user).delete()
        for sport_id in selected_sport_ids:
            UserSportPreference.objects.get_or_create(
                user=request.user,
                sport_id=sport_id
            )

        messages.success(request, 'Your subscriptions have been updated!')
        return redirect('subscriptions')
    
    return redirect('subscriptions')
