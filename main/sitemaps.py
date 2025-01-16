from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Campaign

class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        # Static pages for SEO purposes
        return ['index', 'privacy_policy', 'terms_of_service', 'project_support']

    def location(self, item):
        # Automatically reverse the URL for each static page
        return reverse(item)

class CampaignSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Fetch all campaigns that are publicly visible
        return Campaign.objects.filter(visibility='public')

    def lastmod(self, obj):
        # Use the timestamp field to show when the campaign was last modified
        return obj.timestamp

    def location(self, obj):
        # Use campaign_id instead of slug for the URL
        return reverse('view_campaign', args=[obj.id])  # Using id instead of slug

# Additional Sitemap for more custom or filtered campaigns (optional)
class CustomCampaignSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Filter campaigns based on custom logic (e.g., active campaigns)
        return Campaign.objects.filter(visibility='public', active=True)

    def lastmod(self, obj):
        # Last modified date for active campaigns
        return obj.timestamp

    def location(self, obj):
        # Use campaign_id instead of slug for the URL
        return reverse('view_campaign', args=[obj.id])  # Using id instead of slug
