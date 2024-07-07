from django.contrib import admin
from .models import Profile, Follow, Campaign, Comment, Activity, SupportCampaign, Love, CampaignView, Chat, Message
from .models import  Brainstorming, Donation, AffiliateLink
from .models import ActivityLove, ActivityComment,CampaignProduct
from .models import Notification,Report,NotInterested 
from django.contrib import messages
from .models import Surah, QuranVerse

from .models import Adhkar
from .models import Hadith

from .models import PlatformFund
from .models import Subscriber

from .models import AffiliateLibrary, AffiliateNewsSource
from .models import NativeAd

@admin.register(NativeAd)
class NativeAdAdmin(admin.ModelAdmin):
    list_display = ('title', 'sponsored_by', 'link')  # Customize displayed fields in the list
    search_fields = ('title', 'sponsored_by')  # Add fields for search functionality
    list_filter = ('sponsored_by',)  # Add filters for sponsored_by field
    # You can customize further with fields, list_per_page, etc.



admin.site.register(AffiliateLibrary)
admin.site.register(AffiliateNewsSource)


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)

admin.site.register(Subscriber, SubscriberAdmin)



@admin.register(PlatformFund)
class PlatformFundAdmin(admin.ModelAdmin):
    list_display = ('donation_link',)






class HadithAdmin(admin.ModelAdmin):
    list_display = ('id', 'narrator', 'reference', 'authenticity')
    search_fields = ('narrator', 'reference', 'authenticity')
    list_filter = ('authenticity',)

admin.site.register(Hadith, HadithAdmin)





@admin.register(Adhkar)
class AdhkarAdmin(admin.ModelAdmin):
    list_display = ('type', 'text', 'translation', 'reference')
    search_fields = ('type', 'text', 'translation', 'reference')








@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ('name', 'surah_number')
    search_fields = ('name',)

@admin.register(QuranVerse)
class QuranVerseAdmin(admin.ModelAdmin):
    list_display = ('surah', 'verse_number', 'description')  # Include description here
    search_fields = ('surah__name', 'verse_text', 'translation', 'description')  # Include description here
    list_filter = ('surah',)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'location')  # Display a custom method for verification status
    search_fields = ('user__username', 'bio', 'location')  # Add search functionality for user's username, bio, and location
    readonly_fields = ('user',)  # Make user field read-only

    def has_delete_permission(self, request, obj=None):
        return False  # Disable delete permission in admin

    def has_add_permission(self, request):
        return False  # Disable add permission in admin

admin.site.register(Profile, ProfileAdmin)



class ReportAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'reported_by', 'reason', 'timestamp')
    search_fields = ('campaign__title', 'reported_by__user__username', 'reason')
    list_filter = ('reason', 'timestamp')
    
    actions = ['delete_reported_campaigns']

    def delete_reported_campaigns(self, request, queryset):
        for report in queryset:
            campaign = report.campaign
            campaign_title = campaign.title
            campaign.delete()
            messages.success(request, f'The campaign "{campaign_title}" has been deleted.')

    delete_reported_campaigns.short_description = "Delete selected campaigns"

admin.site.register(Report, ReportAdmin)



# Register the Notification model
admin.site.register(Notification)
admin.site.register(NotInterested)
admin.site.register(Donation)
admin.site.register(AffiliateLink)

admin.site.register(ActivityLove)
admin.site.register(ActivityComment)





@admin.register(CampaignProduct)
class CampaignProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign', 'price', 'stock_quantity', 'is_active')
    list_filter = ('campaign', 'is_active')
    search_fields = ('name', 'description', 'sku')
    list_editable = ('price', 'stock_quantity', 'is_active')







@admin.register(Brainstorming)
class BrainstormingAdmin(admin.ModelAdmin):
    list_display = ('idea', 'supporter', 'campaign')
    search_fields = ('supporter__username', 'campaign__title')
    list_filter = ('campaign',)











@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed')
    search_fields = ('follower__username', 'followed__username')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'timestamp')
    search_fields = ('user__user__username', 'title')
    list_filter = ('timestamp',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'campaign', 'timestamp')
    search_fields = ('user__user__username', 'campaign__title', 'text')
    list_filter = ('timestamp',)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'timestamp')
    search_fields = ('campaign__title', 'content')
    list_filter = ('timestamp',)




class SupportCampaignAdmin(admin.ModelAdmin):
    list_display = ['user', 'campaign', 'donate_monetary_visible', 'attend_event_visible', 'brainstorm_idea_visible','campaign_product_visible']






@admin.register(Love)
class LoveAdmin(admin.ModelAdmin):
    list_display = ('user', 'campaign')
    search_fields = ('user__username', 'campaign__title')

@admin.register(CampaignView)
class CampaignViewAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'user', 'timestamp')  # Remove 'time_spent'
    search_fields = ('campaign__title', 'user__username')
    list_filter = ('timestamp',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    filter_horizontal = ('participants',)  # Allows selecting multiple participants easily
    list_display = ('id', 'created_at')
    search_fields = ('id',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'timestamp', 'content')
    search_fields = ('chat__id', 'sender__username', 'content')
    list_filter = ('timestamp',)
