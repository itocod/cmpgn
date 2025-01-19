from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Campaign

class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = "https"  # Ensure HTTPS is used

    def items(self):
        # List of static pages
        return ['index', 'privacy_policy', 'terms_of_service', 'project_support']

    def location(self, item):
        # Get the URL for each static page
        return reverse(item)

class CampaignSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = "https"  # Ensure HTTPS is used

    def items(self):
        # Fetch all public campaigns
        return Campaign.objects.filter(visibility='public')

    def lastmod(self, obj):
        # Return the timestamp of the last modification
        return obj.timestamp

    def location(self, obj):
        # Generate the URL for the campaign
        return reverse('view_campaign', args=[obj.id])
