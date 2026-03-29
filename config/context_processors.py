from django.conf import settings


def ga_measurement_id(request):
    return {"GA_MEASUREMENT_ID": settings.GA_MEASUREMENT_ID}
