from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from .models import Campaign  # Make sure Campaign model is imported


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['index', 'privacy_policy', 'terms_of_service', 'project_support']

    def location(self, item):
        # Use 'https://' in SITE_URL
        return f"{settings.SITE_URL}{reverse(item)}"

class CampaignSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Campaign.objects.all()

    def lastmod(self, obj):
        return obj.timestamp

    def location(self, obj):
        # Ensure that the URL is correctly prefixed with the site domain
        return f"{settings.SITE_URL}{reverse('view_campaign', args=[obj.id])}"