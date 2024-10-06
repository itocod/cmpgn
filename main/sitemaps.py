from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from .models import Campaign  # Make sure Campaign model is imported

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['index', 'privacy_policy', 'terms_of_service', 'project_support']  # Static view names

    def location(self, item):
        # Manually append the domain for absolute URL generation
        return settings.SITE_URL + reverse(item)

class CampaignSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Campaign.objects.all()

    def lastmod(self, obj):
        return obj.timestamp

    def location(self, obj):
        # Manually append the domain for absolute URL generation
        return settings.SITE_URL + reverse('view_campaign', args=[obj.id])
