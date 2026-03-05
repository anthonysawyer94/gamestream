from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserSubscription


class UserSubscriptionInline(admin.TabularInline):
    model = UserSubscription
    extra = 1


class CustomUserAdmin(UserAdmin):
    inlines = (UserSubscriptionInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
