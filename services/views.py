from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from .models import StreamingService, UserSubscription


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
    user_subs = UserSubscription.objects.filter(user=request.user)
    user_service_ids = set(user_subs.values_list('streaming_service_id', flat=True))

    context = {
        'services': all_services,
        'user_service_ids': user_service_ids,
    }
    return render(request, 'subscriptions.html', context)


@login_required
def update_subscriptions(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('services')

        UserSubscription.objects.filter(user=request.user).delete()

        for service_id in selected_ids:
            UserSubscription.objects.get_or_create(
                user=request.user,
                streaming_service_id=service_id
            )

        messages.success(request, 'Your subscriptions have been updated!')
        return redirect('subscriptions')
    
    return redirect('subscriptions')
