from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Campaign, Profile

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

class ProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"  # Ensure HTTPS is used

    def items(self):
        # Fetch all profiles that should be included in the sitemap
        return Profile.objects.filter(user__is_active=True)  # Example condition, adjust as needed

    def lastmod(self, obj):
        # Use a timestamp field to determine the last modification date
        return obj.user.date_joined  # Or a different field indicating last profile update

    def location(self, obj):
        # Generate the URL for the profile
        return reverse('profile_view', args=[obj.user.username])
