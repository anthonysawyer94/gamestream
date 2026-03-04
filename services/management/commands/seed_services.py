from django.core.management.base import BaseCommand

from services.models import StreamingService

SERVICES = [
    {'name': 'ESPN+', 'slug': 'espn_plus', 'website': 'https://plus.espn.com/'},
    {'name': 'Prime Video', 'slug': 'prime_video', 'website': 'https://www.amazon.com/primevideo'},
    {'name': 'Netflix', 'slug': 'netflix', 'website': 'https://www.netflix.com/'},
    {'name': 'HBO Max', 'slug': 'hbo_max', 'website': 'https://www.max.com/'},
    {'name': 'Paramount+', 'slug': 'paramount_plus', 'website': 'https://www.paramountplus.com/'},
    {'name': 'Apple TV+', 'slug': 'apple_tv', 'website': 'https://tv.apple.com/'},
    {'name': 'Peacock', 'slug': 'peacock', 'website': 'https://www.peacocktv.com/'},
    {'name': 'YouTube TV', 'slug': 'youtube_tv', 'website': 'https://tv.youtube.com/'},
    {'name': 'Hulu + Live TV', 'slug': 'hulu_live', 'website': 'https://www.hulu.com/live-tv'},
    {'name': 'FuboTV', 'slug': 'fubotv', 'website': 'https://www.fubo.tv/'},
]


class Command(BaseCommand):
    help = 'Seed streaming services'

    def handle(self, *args, **options):
        for service in SERVICES:
            obj, created = StreamingService.objects.get_or_create(
                slug=service['slug'],
                defaults=service
            )
            if created:
                self.stdout.write(f"Created {service['name']}")
            else:
                self.stdout.write(f"Already exists: {service['name']}")

        self.stdout.write(self.style.SUCCESS('Streaming services seeded'))
