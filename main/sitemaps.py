from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Campaign

class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return ['index', 'privacy_policy', 'terms_of_service', 'project_support']

    def location(self, item):
        return reverse(item)

class CampaignSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Campaign.objects.all()

    def lastmod(self, obj):
        return obj.updated_at  # Replace with your actual date field

    def location(self, obj):
        # Adjust this to return the URL of the campaign object
        return f"https://rallynex.onrender.com{reverse('view_campaign', args=[obj.id])}"  # Adjust 'campaign_detail' as necessary
