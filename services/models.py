from django.db import models
from django.contrib.auth.models import User


class StreamingService(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    api_key = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "Streaming Services"

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    streaming_service = models.ForeignKey(StreamingService, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'streaming_service')

    def __str__(self):
        return f"{self.user.username} - {self.streaming_service.name}"
