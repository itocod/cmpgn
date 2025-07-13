import paypalrestsdk

import time  # Import the time module

import logging
import json
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from .forms import ActivityFormSet
from django.contrib.auth.models import User
from .forms import (
    UserForm, ProfileForm, CampaignForm, CommentForm, ActivityForm,
    SupportForm, ChatForm, MessageForm, CampaignSearchForm, ProfileSearchForm
)

from .models import (
    Profile, Campaign, Comment, Follow, Activity, SupportCampaign,Brainstorming,
    User, Love, CampaignView, Chat, Notification,Message,CampaignFund
)
from .forms import   BrainstormingForm,CampaignFundForm
from django.http import JsonResponse
from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponseServerError
from django.http import HttpResponse, HttpResponseServerError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.views.generic import CreateView

from django.conf import settings
from decimal import Decimal  # Add this import statement
# Import necessary modules
import os
from dotenv import load_dotenv
from django.urls import reverse
from django.shortcuts import render, redirect

from django.core import exceptions
from django.conf import settings
from .models import Campaign
from django.http import HttpRequest

import paypalrestsdk
from decimal import Decimal
from .models import AffiliateLink
from django.conf import settings

from .utils import calculate_similarity
# views.py
from .forms import ActivityCommentForm
from .models import ActivityComment,ActivityLove

from .models import SupportCampaign, CampaignProduct
from .forms import CampaignProductForm
from django.urls import reverse
from django.utils import timezone

from django.db.models import Case, When, Value, BooleanField

from django.core.files.uploadedfile import SimpleUploadedFile
from mimetypes import guess_type
from .models import  Report
from .forms import ReportForm,NotInterestedForm
from .models import  NotInterested
from django.contrib.admin.views.decorators import staff_member_required
from .models import QuranVerse,Surah
from .models import Adhkar
from .models import Hadith
from .models import PlatformFund,Donation
from .forms import SubscriptionForm,DonationForm
from django.views.decorators.http import require_POST
from .forms import UpdateVisibilityForm

from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import mimetypes

from .models import AffiliateLibrary, AffiliateNewsSource
from .models import NativeAd
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserVerificationForm

from django.db.models import Count



from django.db.models import Count, Q
from itertools import chain
from collections import defaultdict

from django.db.models import Count, Sum
from django.shortcuts import render
from .models import Campaign, ActivityLove, ActivityComment, Brainstorming, Donation


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Case, When, Value, BooleanField, Q
from django.utils import timezone
from .models import Campaign, Profile, Notification, Chat, Message, NativeAd, NotInterested, Love
from django.contrib.auth.models import AnonymousUser

@login_required
def campaign_list(request):
    # Get the current user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Get all campaigns, annotate whether the current user marked them as "not interested"
    campaigns = Campaign.objects.annotate(
        is_not_interested=Case(
            When(not_interested_by__user=user_profile, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    
    # Exclude campaigns that the current user has marked as "not interested"
    public_campaigns = campaigns.filter(
        is_not_interested=False, 
        visibility='public'  # Ensure only public campaigns are displayed
    ).order_by('-timestamp')
    
    # Fetch followed users' campaigns
    following_users = request.user.following.values_list('followed', flat=True)
    followed_campaigns = public_campaigns.filter(user__user__in=following_users)
    
    # Include the current user's own public campaigns
    own_campaigns = public_campaigns.filter(user=user_profile)
    
    # Combine followed campaigns and own campaigns for display
    campaigns_to_display = followed_campaigns | own_campaigns
    
    # Fetch new campaigns from followed users added after the user's last check
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check
    ).exclude(id__in=NotInterested.objects.filter(user=user_profile).values_list('campaign_id', flat=True)).order_by('-timestamp')
    
    # Update the user's last campaign check time
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    # Render the campaign list page
    return render(request, 'revenue/campaign_list.html', {
        'public_campaigns': campaigns_to_display,  # Filtered campaigns to display
        'new_campaigns_from_follows': new_campaigns_from_follows,  # New campaigns ordered by latest
    })












def campaign_engagement_data(request, campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)

    # Aggregating engagement metrics
    donations = Donation.objects.filter(campaign=campaign).aggregate(total=Sum('amount'))['total'] or 0
    views = CampaignView.objects.filter(campaign=campaign).count()
    loves = campaign.loves.count()
    comments = Comment.objects.filter(campaign=campaign).count()
    activities = Activity.objects.filter(campaign=campaign).count()
    activity_loves = ActivityLove.objects.filter(activity__campaign=campaign).count()
    brainstorms = Brainstorming.objects.filter(campaign=campaign).count()
    active_products = CampaignProduct.objects.filter(campaign=campaign, is_active=True).count()
    activity_comments = ActivityComment.objects.filter(activity__campaign=campaign).count()

    # Prepare data
    engagement_data = {
        "donations": donations,
        "views": views,
        "loves": loves,
        "comments": comments,
        "activities": activities,
        "activity_loves": activity_loves,
        "brainstorms": brainstorms,
        "active_products": active_products,
        "activity_comments": activity_comments,  # New data point for Activity Comments
    }

    # Optionally, return as JSON for dynamic updates
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(engagement_data)

    user_profile = get_object_or_404(Profile, user=request.user)
    
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Other data to pass to the template (e.g., unread notifications, ads, etc.)
    form = SubscriptionForm()
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()
    ads = NativeAd.objects.all()
    # Pass data to the template

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

         
    return render(request, 'revenue/engagement_graph.html', {"campaign": campaign, "engagement_data": engagement_data,'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'form': form,
        'ads': ads,
           'suggested_users': suggested_users,
      })



def top_participants_view(request, campaign_id):
    # Fetch the campaign and user profile
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Update last campaign check time
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]

    # Aggregate engagement metrics
    loves = ActivityLove.objects.filter(activity__campaign=campaign).values('user').annotate(total=Count('id'))
    comments = ActivityComment.objects.filter(activity__campaign=campaign).values('user').annotate(total=Count('id'))
    brainstorms = Brainstorming.objects.filter(campaign=campaign).values('supporter').annotate(total=Count('id'))
    donations = Donation.objects.filter(campaign=campaign).values('donor_name').annotate(total=Sum('amount'))

    # Combine all scores for each user
    participant_scores = {}
    for love in loves:
        participant_scores[love['user']] = participant_scores.get(love['user'], 0) + love['total']
    for comment in comments:
        participant_scores[comment['user']] = participant_scores.get(comment['user'], 0) + comment['total']
    for brainstorm in brainstorms:
        participant_scores[brainstorm['supporter']] = participant_scores.get(brainstorm['supporter'], 0) + brainstorm['total']
    for donation in donations:
        participant_scores[donation['donor_name']] = participant_scores.get(donation['donor_name'], 0) + donation['total']

    # Sort participants by score and get top 10
    sorted_participants = sorted(participant_scores.items(), key=lambda x: x[1], reverse=True)
    top_participants = [
        {
            'user': User.objects.get(pk=participant[0]),
            'score': participant[1]
        } for participant in sorted_participants[:10]
    ]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic (site-wide)
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # Other template data
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()
    ads = NativeAd.objects.all()
    form = SubscriptionForm()

    context = {
        'campaign': campaign,
        'top_participants': top_participants,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'form': form,
        'ads': ads,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/top_participants.html', context)


def explore_campaigns(request):
        # Fetch all public campaigns
    public_campaigns = Campaign.objects.filter(visibility='public')  # Adjust this query to match your actual filtering criteria
    
    # Pass the public_campaigns to the template
    return render(request, 'marketing/landing.html', {'public_campaigns': public_campaigns})



def changemakers_view(request):
    # Get all profiles and filter those who are changemakers
    changemakers = [profile for profile in Profile.objects.all() if profile.is_changemaker()]

    return render(request, 'revenue/changemakers.html', {'changemakers': changemakers})


@login_required
def verify_profile(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Other data to pass to the template
    form = SubscriptionForm()
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()
    ads = NativeAd.objects.all()

    if request.method == 'POST':
        form = UserVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(user=request.user)
            
            # Clear existing messages before adding the new one
            storage = messages.get_messages(request)
            storage.used = True

            messages.success(request, 'Your verification request has been submitted successfully.')
            return redirect('verify_profile')
    else:
        form = UserVerificationForm()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with followers count (using the improved logic)
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    context = {
        'form': form,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'ads': ads,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/verify_profile.html', context)

@login_required
def join_leave_campaign(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    profile = request.user.profile

    if campaign in profile.campaigns.all():
        # If the user has already joined the campaign, they leave
        profile.campaigns.remove(campaign)
    else:
        # Otherwise, they join the campaign
        profile.campaigns.add(campaign)

    return redirect('view_campaign', campaign_id=campaign.id)  # Redirect to the campaign detail page





@login_required
def campaign_joiners(request, campaign_id):
    # Get user and campaign data
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    joiners = campaign.user_profiles.all()
    
    # Update last campaign check time
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and messages
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    # Other template data
    form = SubscriptionForm()
    ads = NativeAd.objects.all()

    context = {
        'campaign': campaign,
        'joiners': joiners,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'form': form,
        'ads': ads,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/joiners.html', context)




class CampaignDeleteView(LoginRequiredMixin, DeleteView):
    model = Campaign
    template_name = 'main/campaign_confirm_delete.html'
    success_url = reverse_lazy('manage_campaigns')

    def get_queryset(self):
        user_profile = get_object_or_404(Profile, user=self.request.user)
        return super().get_queryset().filter(user=user_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_filter = self.request.GET.get('category', '')
        user_profile = get_object_or_404(Profile, user=self.request.user)

        # Unread notifications
        unread_notifications = Notification.objects.filter(user=self.request.user, viewed=False)
        context['unread_notifications'] = unread_notifications

        # Unread messages
        user_chats = Chat.objects.filter(participants=self.request.user)
        unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=self.request.user).count()
        context['unread_messages_count'] = unread_messages_count

        # User profile
        context['user_profile'] = user_profile

        # New campaigns from followed users
        following_users = user_profile.following.all()
        new_campaigns_from_follows = Campaign.objects.filter(
            user__user__in=following_users,
            visibility='public',
            timestamp__gt=user_profile.last_campaign_check
        )
        context['new_campaigns_from_follows'] = new_campaigns_from_follows

        # Update campaign check timestamp
        user_profile.last_campaign_check = timezone.now()
        user_profile.save()

        # Improved suggested users logic
        current_user_following = request.user.following.all()  # Get all Follow objects
        following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
        all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
        suggested_users = []
    
        for profile in all_profiles:
            similarity_score = calculate_similarity(user_profile, profile)
            if similarity_score >= 0.5:
                followers_count = Follow.objects.filter(followed=profile.user).count()
                suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
                })

        suggested_users = suggested_users[:2]


        # Ads
        ads = NativeAd.objects.all()
        context['ads'] = ads

        # 🔥 Trending campaigns (Only those with at least 1 love)
        trending_campaigns = Campaign.objects.filter(visibility='public') \
            .annotate(love_count_annotated=Count('loves')) \
            .filter(love_count_annotated__gte=1) \
            .select_related('campaignfund')

        # Apply category filter if provided
        if category_filter:
            trending_campaigns = trending_campaigns.filter(category=category_filter)

        trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]
        context['trending_campaigns'] = trending_campaigns

        # Top Contributors logic
        donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
        love_pairs = Love.objects.values_list('user_id', 'campaign_id')
        comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
        view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
        brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
        activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
        activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

        # Combine all engagement pairs
        all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                         brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

        # Count number of unique campaigns each user engaged with
        user_campaign_map = defaultdict(set)
        for user_id, campaign_id in all_pairs:
            user_campaign_map[user_id].add(campaign_id)

        # Build a list of contributors with their campaign engagement count
        contributor_data = []
        for user_id, campaign_set in user_campaign_map.items():
            try:
                profile = Profile.objects.get(user__id=user_id)
                contributor_data.append({
                    'user': profile.user,
                    'image': profile.image,
                    'campaign_count': len(campaign_set),
                })
            except Profile.DoesNotExist:
                continue

        # Sort contributors by campaign_count descending
        top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]
        context['top_contributors'] = top_contributors

        # Categories
        categories = Campaign.objects.values_list('category', flat=True).distinct()
        context['categories'] = categories
        context['selected_category'] = category_filter

        return context








def native_ad_list(request):
    ads = NativeAd.objects.all()
    return render(request, 'native_ad_list.html', {'ads': ads})

def native_ad_detail(request, ad_id):
    ad = get_object_or_404(NativeAd, pk=ad_id)
    return render(request, 'native_ad_detail.html', {'ad': ad})





def library_affiliates(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    libraries = AffiliateLibrary.objects.all()
    ads = NativeAd.objects.all() 

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

          
    return render(request, 'affiliate/library_affiliates.html', {'ads':ads,'libraries': libraries,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows,  'suggested_users': suggested_users,
         })

def news_affiliates(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    news_sources = AffiliateNewsSource.objects.all()
    ads = NativeAd.objects.all() 

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

          
    return render(request, 'affiliate/news_affiliates.html', {'ads':ads,'news_sources': news_sources,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows,  'suggested_users': suggested_users,
         })






@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = default_storage.save(file.name, ContentFile(file.read()))
        file_url = default_storage.url(file_name)
        file_mime_type, _ = mimetypes.guess_type(file_url)
        return JsonResponse({'location': file_url, 'type': file_mime_type})
    return JsonResponse({'error': 'File upload failed'}, status=400)



class CustomLoginView(LoginView):
    def get_success_url(self):
        return reverse_lazy('rallynex_logo')



@login_required
def rallynex_logo(request):
    return render(request, 'main/rallynex_logo.html')








def subscribe(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have successfully subscribed!')
            return redirect('home')  # Change 'home' to the name of your home view
    else:
        form = SubscriptionForm()
    return render(request, 'revenue/subscribe.html', {'form': form})


    

def jobs(request):
    return render(request, 'revenue/jobs.html')

def events(request):
    return render(request, 'revenue/events.html')

def privacy_policy(request):
    return render(request, 'revenue/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'revenue/terms_of_service.html')

def project_support(request):
    return render(request, 'revenue/support.html')



def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /tinymce/",
        "Disallow: /static/",
        "Allow: /",
        "",
        "Sitemap: https://rallynex.onrender.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")



def platformfund_view(request):
    if request.user.is_authenticated:
        following_users = [follow.followed for follow in request.user.following.all()]  
        user_profile = get_object_or_404(Profile, user=request.user)
        unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
        
        # Check if there are new campaigns from follows
        new_campaigns_from_follows = Campaign.objects.filter(
            user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check
        )

        # Update last_campaign_check for the user's profile
        user_profile.last_campaign_check = timezone.now()
        user_profile.save()
    else:
        following_users = []
        user_profile = None
        unread_notifications = []
        new_campaigns_from_follows = []

    platformfunds = PlatformFund.objects.all()
    ads = NativeAd.objects.all()  

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

          
    return render(request, 'revenue/platformfund.html', {
        'ads': ads,
        'platformfunds': platformfunds,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
          'suggested_users': suggested_users,
        
    })





@login_required
def hadith_list(request):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Hadith data
    hadiths = Hadith.objects.all()
    
    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'hadiths': hadiths,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/hadith_list.html', context)

@login_required
def hadith_detail(request, hadith_id):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Hadith data
    hadith = get_object_or_404(Hadith, pk=hadith_id)
    
    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'hadith': hadith,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/hadith_detail.html', context)

@login_required
def adhkar_list(request):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Adhkar data
    adhkars = Adhkar.objects.all()
    
    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'adhkars': adhkars,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/adhkar_list.html', context)




@login_required
def adhkar_detail(request, adhkar_id):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Adhkar data
    adhkar = get_object_or_404(Adhkar, id=adhkar_id)
    
    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'adhkar': adhkar,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/adhkar_detail.html', context)





@login_required
def quran_view(request):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Quran data
    surahs = Surah.objects.all()
    quran_verses = QuranVerse.objects.all()
    
    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'surahs': surahs,
        'quran_verses': quran_verses,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/quran.html', context)


@login_required
def mark_not_interested(request, campaign_id):
    campaign = Campaign.objects.get(pk=campaign_id)
    user_profile = request.user.profile
    
    # Check if the user has already marked this campaign as not interested
    existing_entry = NotInterested.objects.filter(user=user_profile, campaign=campaign).exists()
    
    if not existing_entry:
        # If not, create a new entry
        not_interested_entry = NotInterested.objects.create(user=user_profile, campaign=campaign)
        not_interested_entry.save()
    
    # Redirect back to the campaign detail page or any other appropriate page
    return redirect('home')

@login_required
def report_campaign(request, campaign_id):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Handle form submission
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.campaign = campaign
            report.reported_by = request.user.profile
            report.save()
            messages.success(request, 'Thank you for reporting. We will review your report shortly.')
            return redirect('view_campaign', campaign_id=campaign.id)
    else:
        form = ReportForm()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'form': form,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/report_campaign.html', context)




def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        # Save the image to the desired location or process it as needed
        # Example: activity.image = image_file; activity.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})





@login_required
def product_manage(request, campaign_id=None, product_id=None):
    # Initialize variables
    campaign = None
    product = None

    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    user_profile = get_object_or_404(Profile, user=request.user)

    # Fetch campaign and product if IDs are provided
    if campaign_id:
        campaign = get_object_or_404(Campaign, pk=campaign_id)
    if product_id:
        product = get_object_or_404(CampaignProduct, pk=product_id)

    # Handle form submission
    if request.method == 'POST':
        form = CampaignProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.campaign = campaign
            product.save()
            if campaign:
                return redirect('product_manage', campaign_id=campaign.id)
            else:
                return redirect('product_manage')
    else:
        form = CampaignProductForm(instance=product)
    
    # Fetch all products for the campaign
    products = CampaignProduct.objects.filter(campaign=campaign).order_by('-date_added') if campaign else None
    product_count = products.count() if products else 0

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # User notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'form': form,
        'product': product,
        'campaign': campaign,
        'products': products,
        'product_count': product_count,
        'unread_notifications': unread_notifications,
        'user_profile': user_profile,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/product_manage.html', context)


def love_activity(request, activity_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            activity = Activity.objects.get(id=activity_id)
            # Check if the user has already loved this activity
            if not ActivityLove.objects.filter(activity=activity, user=request.user).exists():
                # Create a new love for this activity by the user
                ActivityLove.objects.create(activity=activity, user=request.user)
            # Get updated love count for the activity
            love_count = activity.loves.count()
            return JsonResponse({'love_count': love_count})
        except Activity.DoesNotExist:
            return JsonResponse({'error': 'Activity not found'}, status=404)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)







def activity_detail(request, activity_id):
    # Get basic objects
    user_profile = get_object_or_404(Profile, user=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    # Notification and messaging data
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    
    # Update last check time
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Suggested users logic
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'activity': activity,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/activity_detail.html', context)






def add_activity_comment(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    if request.method == 'POST':
        form = ActivityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.activity = activity
            comment.user = request.user
            comment.save()
            return JsonResponse({
                'success': True, 
                'content': comment.content, 
                'username': comment.user.username, 
                'timestamp': comment.timestamp,
                'profile_image_url': comment.user.profile.image.url
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        comments = activity.activitycomment_set.all().order_by('-timestamp')
        form = ActivityCommentForm()
        
        context = {
            'activity': activity, 
            'comments': comments, 
            'form': form,
            'user_profile': user_profile,
            'unread_notifications': unread_notifications,
            'new_campaigns_from_follows': new_campaigns_from_follows,
            'ads': ads,
            'suggested_users': suggested_users,
            'trending_campaigns': trending_campaigns,
            'top_contributors': top_contributors,
            'categories': categories,
            'selected_category': category_filter,
        }
        
        return render(request, 'main/add_activity_comment.html', context)



@login_required
def suggest(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Improved: Get followed user IDs explicitly
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Get all profiles except the current user's and those they're following
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)

    # Suggested users based on similarity score
    suggested_users = []
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count,
                'similarity_score': similarity_score  # Optional: include for debugging
            })
    
    # Sort by similarity score (highest first) and take top 20 for the suggestions page
    suggested_users = sorted(suggested_users, key=lambda x: x['similarity_score'], reverse=True)[:20]

    # Unread notifications
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    # New campaigns from followed users (using the same following_user_ids)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last check timestamp
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Trending campaigns
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic (unchanged)
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Ads
    ads = NativeAd.objects.all()

    return render(request, 'main/suggest.html', {
        'ads': ads,
        'suggested_users': suggested_users,  # Fixed typo from 'suggested_users'
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    })



@login_required
def affiliate_links(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Get all affiliate links sorted by the newest first
    affiliate_links = AffiliateLink.objects.all().order_by('-created_at')

    # Fetch ads if necessary
    ads = NativeAd.objects.all()  
    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # Return the rendered response
    return render(request, 'revenue/affiliate_links.html', {
        'ads': ads,
        'affiliate_links': affiliate_links,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
          'suggested_users': suggested_users,
      
    })





@login_required
def update_visibility(request, campaign_id):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Fetch unread notifications
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except ObjectDoesNotExist:
        return HttpResponseServerError("Campaign not found")

    # Get all support campaigns
    support_campaigns = SupportCampaign.objects.filter(campaign_id=campaign_id)

    if request.method == 'POST':
        # Update visibility settings
        for support_campaign in support_campaigns:
            support_campaign.donate_monetary_visible = request.POST.get('donate_monetary_visible', False) == 'on'
            support_campaign.share_social_media_visible = request.POST.get('share_social_media_visible', False) == 'on'
            support_campaign.provide_resource_visible = request.POST.get('provide_resource_visible', False) == 'on'
            support_campaign.brainstorm_idea_visible = request.POST.get('brainstorm_idea_visible', False) == 'on'
            support_campaign.campaign_product_visible = request.POST.get('campaign_product_visible', False) == 'on'
            support_campaign.save()
        return redirect('support', campaign_id=campaign_id)

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # New campaigns from follows (using the same following_user_ids)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'support_campaigns': support_campaigns,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/update_visibility.html', context)




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Campaign, Profile, SupportCampaign, CampaignProduct, NativeAd, Notification






@login_required
def support(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    campaign = get_object_or_404(Campaign, id=campaign_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Retrieve or create the SupportCampaign object
    support_campaign, created = SupportCampaign.objects.get_or_create(
        user=request.user, 
        campaign=campaign
    )
    
    # Get products related to the campaign
    products = CampaignProduct.objects.filter(campaign=campaign) if campaign else None
    
    # Notification and follows data
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    
    # Update last check time
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'campaign': campaign,
        'support_campaign': support_campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'products': products,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/support.html', context)





@login_required
def update_hidden_links(request):
    if request.method == 'POST':
        link_name = request.POST.get('link_name')
        campaign_id = request.POST.get('campaign_id')
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            # Check if the user is the owner of the campaign
            if request.user == campaign.user.user:
                # Update the visibility status of the link based on link_name
                if link_name == 'donate_monetary':
                    campaign.donate_monetary_visible = False
        
                elif link_name == 'brainstorm_idea':
                    campaign.brainstorm_idea_visible = False
                elif link_name == 'campaign_product':
                    campaign.campaign_product_visible = False
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid link name'})
                campaign.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'User is not the owner of the campaign'})
        except Campaign.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Campaign not found'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})








def brainstorm_idea(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    campaign = get_object_or_404(Campaign, id=campaign_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    if request.method == 'POST':
        form = BrainstormingForm(request.POST, request.FILES)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.supporter = request.user
            idea.campaign = campaign
            idea.save()
            return redirect('brainstorm_idea', campaign_id=campaign.id)
        else:
            messages.error(request, "Please fix the errors in your submission.")
    else:
        form = BrainstormingForm()

    ideas_for_campaign = Brainstorming.objects.filter(campaign=campaign).order_by('-pk')

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'form': form,
        'ideas_for_campaign': ideas_for_campaign,
        'user_profile': user_profile,
        'campaign': campaign,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,  # Fixed typo from 'suggested_users'
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/brainstorm.html', context)







@login_required
def donate_monetary(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/donate_monetary.html', context)






def support_campaign_create(request):
    if request.method == 'POST':
        form = SupportCampaignForm(request.POST)
        if form.is_valid():
            support_campaign = form.save(commit=False)
            support_campaign.user = request.user
            support_campaign.save()
            return redirect('success_url')  # Redirect to a success URL
    else:
        form = SupportCampaignForm()
    campaign_products = CampaignProduct.objects.all()  # Retrieve all campaign products
    return render(request, 'support_campaign_create.html', {'form': form, 'campaign_products': campaign_products})






def fill_paypal_account(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('campaigns_list')  # Redirect to campaigns list or any other appropriate page
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'main/fill_paypal_account.html', {'form': form})




@login_required
def search_campaign(request):
    # Get user data with improved following logic
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    user_profile = get_object_or_404(Profile, user=request.user)
    query = request.GET.get('search_query')
    
    # Initialize empty querysets for all searchable models
    campaigns = Campaign.objects.none()
    profiles = Profile.objects.none()
    quran_verses = QuranVerse.objects.none()
    adhkar = Adhkar.objects.none()
    hadiths = Hadith.objects.none()
    
    if query:
        # Search across different models
        campaigns = Campaign.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(category__icontains=query)
        )
        profiles = Profile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(bio__icontains=query)
        )
        quran_verses = QuranVerse.objects.filter(
            Q(verse_text__icontains=query) |
            Q(translation__icontains=query) |
            Q(description__icontains=query) |
            Q(surah__name__icontains=query)
        )
        adhkar = Adhkar.objects.filter(
            Q(type__icontains=query) |
            Q(text__icontains=query) |
            Q(translation__icontains=query) |
            Q(reference__icontains=query)
        )
        hadiths = Hadith.objects.filter(
            Q(narrator__icontains=query) |
            Q(text__icontains=query) |
            Q(reference__icontains=query) |
            Q(authenticity__icontains=query)
        )
    
    # Notifications handling
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    unread_notifications = notifications.filter(viewed=False)
    unread_notifications.update(viewed=True)
    unread_count = unread_notifications.count()
    
    # New campaigns from follows using consistent following_user_ids
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'campaigns': campaigns,
        'profiles': profiles,
        'quran_verses': quran_verses,
        'adhkar': adhkar,
        'hadiths': hadiths,
        'user_profile': user_profile,
        'unread_count': unread_count,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'search_query': query,  # Pass the search query back to template
    }
    
    return render(request, 'main/search_results.html', context)

@login_required
def notification_list(request):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    # Retrieve notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    # Mark notifications as viewed
    unread_notifications = notifications.filter(viewed=False)
    unread_notifications.update(viewed=True)

    # Count unread notifications
    unread_count = unread_notifications.count()
    
    # Check if there are new campaigns from follows (using consistent following_user_ids)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()
    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'notifications': notifications,
        'user_profile': user_profile,
        'unread_count': unread_count,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    return render(request, 'main/notification_list.html', context)


@login_required
def create_chat(request):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ChatForm(request.user, request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.manager = request.user
            chat.save()
            form.save_m2m()
            return redirect('chat_detail', chat_id=chat.id)
    else:
        form = ChatForm(request.user)
    
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'form': form,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/create_chat.html', context)






@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(
        Chat.objects.select_related("manager").prefetch_related("participants"),
        id=chat_id
    )
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = request.user.following.values_list('followed', flat=True)
    followers = request.user.followers.values_list('follower', flat=True)

    combined_users = set(following_users) | set(followers)

    user_choices = User.objects.filter(pk__in=combined_users).exclude(
        pk=request.user.pk
    ).exclude(pk__in=chat.participants.values_list("pk", flat=True))

    messages = Message.objects.filter(chat=chat).select_related("sender__profile").order_by('timestamp')[:50]

    if request.method == 'POST':
        message_form = MessageForm(request.POST, request.FILES)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.sender = request.user
            message.chat = chat
            message.save()
            return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})
        return JsonResponse({'status': 'error', 'message': 'Form data is invalid', 'errors': message_form.errors})

    message_form = MessageForm(initial={'chat': chat})

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)[:10]
    new_campaigns_from_follows = Campaign.objects.filter(
        user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check
    )

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'user_profile': user_profile,
        'chat': chat,
        'message_form': message_form,
        'messages': messages,
        'user_choices': user_choices,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }

    return render(request, 'main/chat_detail.html', context)




@login_required
def user_chats(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    last_chat_check = user_profile.last_chat_check

    # Update user's last chat check timestamp
    user_profile.last_chat_check = timezone.now()
    user_profile.save()

    # Get user chats and check for unread messages
    user_chats = Chat.objects.filter(participants=request.user) | Chat.objects.filter(manager=request.user)
    for chat in user_chats:
        chat.has_unread_messages = chat.messages.filter(timestamp__gt=last_chat_check).exists()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with improved logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # Other data
    following_users = [follow.followed for follow in request.user.following.all()]
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,  # Updated to use the same following_user_ids
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'user_chats': user_chats,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/user_chats.html', context)


@require_POST
@login_required
def add_participants(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user == chat.manager:
        user_ids = request.POST.getlist('participants')
        users_to_add = User.objects.filter(id__in=user_ids)
        chat.participants.add(*users_to_add)
    return redirect('chat_detail', chat_id=chat_id)

@require_POST
@login_required
def remove_participants(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user == chat.manager:
        user_ids = request.POST.getlist('participants')
        users_to_remove = chat.participants.filter(id__in=user_ids)
        chat.participants.remove(*users_to_remove)
    return redirect('chat_detail', chat_id=chat_id)

@require_POST
@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user == chat.manager:
        chat.delete()
    return redirect('user_chats')





@login_required
def view_campaign(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    user_profile = None
    already_loved = False

    if request.user.is_authenticated:
        user_profile = request.user.profile
        already_loved = Love.objects.filter(user=request.user, campaign=campaign).exists()

        if not CampaignView.objects.filter(user=user_profile, campaign=campaign).exists():
            CampaignView.objects.create(user=user_profile, campaign=campaign)

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Get suggested users with followers count
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'campaign': campaign,
        'ads': ads,
        'user_profile': user_profile,
        'already_loved': already_loved,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }

    return render(request, 'main/campaign_detail.html', context)





def campaign_detail(request, pk):
    # Retrieve the campaign object using its primary key (pk)
    campaign = get_object_or_404(Campaign, pk=pk)
    form = SubscriptionForm()
    # Pass the campaign object to the template for rendering
    return render(request, 'main/campaign_detail.html', {'campaign': campaign,'form':form})















def thank_you(request):
    
    return render(request, 'main/thank_you.html')






def activity_list(request, campaign_id):
    # Get data from request
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Get all activities associated with the campaign
    activities = Activity.objects.filter(campaign=campaign).order_by('-timestamp')
    
    # Add comment count for each activity
    for activity in activities:
        activity.comment_count = ActivityComment.objects.filter(activity=activity).count()
    
    # List of image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    activity_count = activities.count()
    
    # Notification and messaging data
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'campaign': campaign, 
        'activities': activities, 
        'image_extensions': image_extensions,
        'user_profile': user_profile,
        'activity_count': activity_count,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/activity_list.html', context)





# views.py
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from .models import ActivityComment, ActivityCommentLike
from django.db.models import Count

@require_GET
@login_required
def get_activity_comments(request, activity_id):
    try:
        activity = Activity.objects.get(id=activity_id)
        load_all = request.GET.get('all', 'false').lower() == 'true'
        
        # Get base queryset
        comments = ActivityComment.objects.filter(activity=activity)
        
        # Count total comments
        total_comments = comments.count()
        
        # Get either all or just the 2 most recent comments
        if not load_all and total_comments > 2:
            comments = comments.order_by('-timestamp')[:2]
        
        # Prepare comment data
        comments_data = []
        for comment in comments:
            comments_data.append({
                'id': comment.id,
                'username': comment.user.username,
                'user_image': comment.user.profile.image.url if comment.user.profile.image else '',
                'content': comment.content,
                'timestamp': timezone.localtime(comment.timestamp).strftime('%b %d, %Y at %I:%M %p'),
                'like_count': ActivityCommentLike.objects.filter(comment=comment).count(),
                'liked': ActivityCommentLike.objects.filter(comment=comment, user=request.user).exists()
            })
        
        # Return newest first
        comments_data.reverse()
        
        return JsonResponse({
            'success': True,
            'comments': comments_data,
            'total_comments': total_comments
        })
    except Activity.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Activity not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_POST
def post_activity_comment(request):
    try:
        data = json.loads(request.body)
        activity_id = data.get('activity_id')
        content = data.get('content')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})
            
        activity = Activity.objects.get(id=activity_id)
        comment = ActivityComment.objects.create(
            activity=activity,
            user=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'comment_id': comment.id
        })
        
    except Activity.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Activity not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})







@require_POST
@login_required
def like_activity_comment(request):
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        action = data.get('action')
        
        if not comment_id or not action:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        comment = ActivityComment.objects.get(id=comment_id)
        
        if action == 'like':
            # Check if already liked
            if not ActivityCommentLike.objects.filter(comment=comment, user=request.user).exists():
                ActivityCommentLike.objects.create(comment=comment, user=request.user)
        elif action == 'unlike':
            ActivityCommentLike.objects.filter(comment=comment, user=request.user).delete()
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        # Get updated like count
        like_count = ActivityCommentLike.objects.filter(comment=comment).count()
        
        return JsonResponse({
            'success': True,
            'like_count': like_count
        })
    except ActivityComment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
import json
from .models import ActivityComment
from django.shortcuts import get_object_or_404

@require_POST
@login_required
@csrf_exempt
def post_comment_reply(request):
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        content = data.get('content')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        parent_comment = get_object_or_404(ActivityComment, id=comment_id)
        reply = ActivityComment.objects.create(
            activity=parent_comment.activity,
            user=request.user,
            content=content,
            parent_comment=parent_comment
        )
        
        return JsonResponse({
            'success': True,
            'reply': {
                'id': reply.id,
                'content': reply.content,
                'username': reply.user.username,
                'user_image': reply.user.profile.image.url if hasattr(reply.user, 'profile') and reply.user.profile.image else '',
                'timestamp': reply.timestamp.strftime('%b %d, %Y %I:%M %p'),
                'like_count': reply.like_count,
                'liked': False  # New replies aren't liked by default
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_GET
@login_required
def get_comment_replies(request, comment_id):
    try:
        parent_comment = get_object_or_404(ActivityComment, id=comment_id)
        replies = parent_comment.replies.all().order_by('timestamp')
        
        replies_data = []
        for reply in replies:
            replies_data.append({
                'id': reply.id,
                'content': reply.content,
                'username': reply.user.username,
                'user_image': reply.user.profile.image.url if hasattr(reply.user, 'profile') and reply.user.profile.image else '',
                'timestamp': reply.timestamp.strftime('%b %d, %Y %I:%M %p'),
                'like_count': reply.like_count,
                'liked': request.user in reply.likes.all()
            })
        
        return JsonResponse({
            'success': True,
            'replies': replies_data,
            'total_replies': parent_comment.reply_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




@require_POST
@login_required
@csrf_exempt
def like_comment_reply(request):
    try:
        data = json.loads(request.body)
        reply_id = data.get('reply_id')
        action = data.get('action')  # 'like' or 'unlike'
        
        if action not in ['like', 'unlike']:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        reply = get_object_or_404(ActivityComment, id=reply_id)
        
        if action == 'like':
            # Using the ActivityCommentLike model
            if not ActivityCommentLike.objects.filter(comment=reply, user=request.user).exists():
                ActivityCommentLike.objects.create(comment=reply, user=request.user)
        else:
            ActivityCommentLike.objects.filter(comment=reply, user=request.user).delete()
        
        return JsonResponse({
            'success': True,
            'like_count': ActivityCommentLike.objects.filter(comment=reply).count(),
            'action': action
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def create_activity(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)

    if request.method == 'POST':
        formset = ActivityFormSet(request.POST, request.FILES, instance=campaign)
        if formset.is_valid():
            formset.save()
            return redirect('activity_list', campaign_id=campaign_id)
    else:
        formset = ActivityFormSet(instance=campaign)

    # Notification and messaging data
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()

    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    # Expanded list of 200 emojis for activities
    emojis = [
    '📢', '🎉', '💼', '📊', '💡', '🔍', '📣', '🎯', '🔔', '📱', '💸', '⭐', '💥', '🌟', 
    '🌳', '🌍', '🌱', '🌲', '🌿', '🍃', '🏞️', '🦋', '🐝', '🐞', '🦜', '🐢', '🐘', '🐆', '🐅', '🐬',  # Environmental and wildlife
    '💉', '❤️', '🩺', '🚑', '🏥', '🧬', '💊', '🩹', '🧑‍⚕️', '👨‍⚕️', '🩸', '🫁', '🫀', '🧠', '🦷', '👁️',  # Health and wellness
    '📚', '🎓', '🏫', '🖊️', '📖', '✍️', '🧑‍🏫', '👨‍🏫', '📜', '🔖', '📕', '📝', '📋', '📑', '🧮', '🎒',  # Education and literacy
    '🤝', '🗣️', '💬', '🏘️', '🏠', '👩‍🏫', '👨‍🏫', '🧑‍🎓', '👩‍🎓', '👨‍🎓', '🏘️', '🏡', '🏙️', '🚪', '🛠️', '🛏️',  # Community development
    '⚖️', '🕊️', '🏳️‍🌈', '🔒', '🛡️', '📜', '📛', '🤲', '✌️', '👐', '🙏', '🧑‍⚖️', '👨‍⚖️', '📝', '🪧', '🎗️',  # Equality and inclusion
    '🐾', '🐕', '🐈', '🐅', '🐆', '🐘', '🐄', '🐑', '🐇', '🐿️', '🐦', '🦢', '🦉', '🐠', '🦑', '🦓', '🐅',  # Animal welfare
    '🌐', '💻', '📱', '🖥️', '⌨️', '🔐', '🛡️', '📡', '🛰️', '🌐', '💾', '🖱️', '🖨️', '📂', '🗄️', '📧', '🛠️',  # Digital rights and tech
    '🌍', '🛠️', '📜', '🌱', '💡', '🏡', '🏘️', '🏭', '🚜', '🚲', '🌾', '💧', '🌊', '☀️', '⚡', '💨', '🌋',  # Sustainable development
    '🕊️', '🔫', '💣', '⚔️', '🛡️', '🕵️‍♂️', '🕵️‍♀️', '🚨', '🚔', '🧑‍✈️', '👮‍♂️', '👮‍♀️', '🧑‍✈️', '🎯', '✌️', '☮️', '📜',  # Peace and conflict resolution
    '📱', '📡', '🌐', '💻', '🔐', '🔒', '🛡️', '📊', '📈', '🖥️', '🗂️', '📂', '🖱️', '🖨️', '📞', '💡', '🔍',  # Economic empowerment and digital advocacy
    '💸', '💰', '🏦', '🏛️', '🧑‍💼', '👨‍💼', '📈', '🧾', '📜', '💼', '📊', '🧑‍💻', '👨‍💻', '🏦', '💳', '💱',  # Economic empowerment
    '🎨', '🎭', '🎬', '🎤', '🎻', '🎷', '🎺', '🎸', '🎹', '🎧', '📸', '📹', '🎥', '🖼️', '🧑‍🎨', '👨‍🎨',  # Artistic advocacy and creatives
    '🛠️', '🧑‍🔧', '👨‍🔧', '🏗️', '🧑‍🏭', '🚜', '⚙️', '🔩', '🔧', '🪛', '🛢️', '🏭', '🚇', '🚉', '🛠️', '🔧',  # Infrastructure and development
    '🏆', '🎯', '📜', '🎗️', '🎖️', '🏅', '🥇', '🥈', '🥉', '📣', '🚀', '⚡', '🌟', '⭐', '🔔', '💡',  # Recognition, achievement, and awards
    '🎡', '🎢', '🎪', '🎬', '🎤', '🎧', '📽️', '📺', '🎭', '🎨', '🖼️', '🎷', '🎸', '🎹', '🎤', '🎬',  # Creative, events, and entertainment
    '📝', '📄', '📊', '📈', '🗣️', '🗳️', '📋', '🧾', '🧑‍⚖️', '👨‍⚖️', '🏛️', '📜', '✍️', '📝', '📋', '✏️',  # Policy advocacy, legal, and campaigns
    '🖋️', '🖊️', '🖌️', '🧑‍🎨', '👨‍🎨', '🎨', '📸', '🎥', '🎤', '📹', '🖼️', '🎭', '🎬', '🎤', '🎹', '🎨',  # Creative activities
    '🏗️', '🚜', '🛠️', '🔧', '⚙️', '📊', '📈', '💡', '🛠️', '🏛️', '🏦', '💼', '🧑‍💻', '🧑‍⚖️', '📜', '📋',  # Development and advocacy
    '🎗️', '🚩', '🏁', '📢', '🎯', '🎉', '💼', '📊', '💡', '🔍', '📣', '🎯', '🔔', '📱', '💸', '⭐', '💥',  # Miscellaneous activities and objectives
    '🧑‍🚒', '👨‍🚒', '🚒', '🧑‍🚒', '🚨', '🚑', '🏥', '💉', '❤️', '🩸', '🩺', '👩‍⚕️', '👨‍⚕️', '🏥', '🚨', '🧑‍⚕️',  # Emergency and humanitarian aid
    ]

    # Split the emojis into two parts: first 10 and the rest
    initial_emojis = emojis[:10]
    additional_emojis = emojis[10:]

    context = {
        'ads': ads,
        'formset': formset,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'initial_emojis': initial_emojis,
        'additional_emojis': additional_emojis,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }

    return render(request, 'main/activity_create.html', context)


@login_required
def manage_campaigns(request):
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Get selected category filter from request
    category_filter = request.GET.get('category', '')

    # Fetch all campaigns (both public and private) for the current user's profile
    all_campaigns = Campaign.objects.filter(user=user_profile)
    
    # Apply category filter if provided
    if category_filter:
        all_campaigns = all_campaigns.filter(category=category_filter)

    all_campaigns = all_campaigns.order_by('-timestamp')

    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows
    following_users = [follow.followed for follow in request.user.following.all()]
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()
    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]


    # Fetch available categories
    categories = Campaign.objects.filter(user=user_profile).values_list('category', flat=True).distinct()

    return render(request, 'main/manage_campaigns.html', {
        'ads': ads,
        'campaigns': all_campaigns,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'categories': categories,  # Pass categories to template
        'selected_category': category_filter,  # Retain selected category
          'suggested_users': suggested_users,
 
    })


@login_required
def private_campaign(request):
    # Get user and profile data with improved following logic
    user_profile = get_object_or_404(Profile, user=request.user)
    category_filter = request.GET.get('category', '')
    
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]

    # Get private campaigns with not_interested annotation
    campaigns = Campaign.objects.annotate(
        is_not_interested=Case(
            When(not_interested_by__user=user_profile, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )

    # Filter visible private campaigns using following_user_ids
    visible_campaigns = campaigns.filter(
        Q(user__user__id__in=following_user_ids) | Q(user=user_profile),
        visibility='private',
        is_not_interested=False
    ).filter(
        Q(visible_to_followers=user_profile) | Q(user=user_profile)
    )

    # Apply category filter if provided
    if category_filter:
        visible_campaigns = visible_campaigns.filter(category=category_filter)

    visible_campaigns = visible_campaigns.order_by('-timestamp')

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and messages
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()

    # New campaigns from follows using consistent following_user_ids
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids, 
        visibility='private', 
        timestamp__gt=user_profile.last_campaign_check
    ).exclude(id__in=NotInterested.objects.filter(user=user_profile).values_list('campaign_id', flat=True)) \
     .order_by('-timestamp')

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    # Ads and categories
    ads = NativeAd.objects.all()
    categories = Campaign.objects.filter(
        Q(user__user__id__in=following_user_ids) | Q(user=user_profile),
        visibility='private'
    ).values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'private_campaigns': visible_campaigns,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'unread_messages_count': unread_messages_count,
        'categories': categories,
        'selected_category': category_filter,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/private_campaign.html', context)

import time

@login_required
def update_visibilit(request, campaign_id):
    start_time = time.time()  # Start timing

    # Get user and campaign data
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    # Get followers for visibility settings
    followers = Profile.objects.filter(user__in=Follow.objects.filter(followed=request.user).values('follower'))
    campaign = get_object_or_404(Campaign, pk=campaign_id, user=user_profile)

    # Handle form submission
    if request.method == 'POST':
        form = UpdateVisibilityForm(request.POST, instance=campaign, followers=followers)
        if form.is_valid():
            campaign = form.save(commit=False)
            if campaign.visibility == 'private':
                campaign.visible_to_followers.set(form.cleaned_data['followers_visibility'])
            campaign.save()
            return redirect('private_campaign')
    else:
        form = UpdateVisibilityForm(instance=campaign, followers=followers)

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    end_time = time.time()  # End timing
    print(f"Form processing took {end_time - start_time} seconds")

    context = {
        'form': form,
        'campaign': campaign,
        'ads': ads,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/manage_campaign_visibility.html', context)
@login_required
def delete_campaign(request, campaign_id):
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
        # Check if the current user is the owner of the campaign
        if request.user == campaign.user.user:
            # Delete the campaign
            campaign.delete()
        else:
            # Raise 403 Forbidden if the current user is not the owner of the campaign
            raise Http404("You are not allowed to delete this campaign.")
    except Campaign.DoesNotExist:
        raise Http404("Campaign does not exist.")
    
    # Redirect to a relevant page after deleting the campaign
    return redirect('private_campaign')








def success_page(request):
    return render(request, 'main/success_page.html')





def toggle_love(request, campaign_id):
    if request.method == 'POST' and request.user.is_authenticated:
        campaign = get_object_or_404(Campaign, pk=campaign_id)
        user = request.user

        # Check if the user has already loved the campaign
        if Love.objects.filter(campaign=campaign, user=user).exists():
            # User has loved the campaign, remove the love
            Love.objects.filter(campaign=campaign, user=user).delete()
            love_count = campaign.love_count
        else:
            # User hasn't loved the campaign, add the love
            Love.objects.create(campaign=campaign, user=user)
            love_count = campaign.love_count

        # Return updated love count
        return JsonResponse({'love_count': love_count})

    # If the request method is not POST or user is not authenticated, return 404
    return JsonResponse({}, status=404)

from .models import CommentLike  # Adjust path if it's in another app

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Campaign
from django.db.models import Count, Case, When, Value, Q
from django.db.models.fields import CharField

# views.py
from django.http import JsonResponse

def record_campaign_view(request, campaign_id):
    if request.method == 'POST':
        # Handle logic (e.g., increment views)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required
def get_comments(request):
    campaign_id = request.GET.get('campaign_id')
    if not campaign_id:
        return JsonResponse({'error': 'Campaign ID is required'}, status=400)
    
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
        # Get top-level comments (not replies)
        comments = campaign.comments.filter(parent_comment__isnull=True).annotate(
            like_count=Count('likes', filter=Q(likes__is_like=True)),
            dislike_count=Count('likes', filter=Q(likes__is_like=False)),
            reply_count=Count('replies'),
            user_like_status=Case(
                When(likes__user=request.user.profile, likes__is_like=True, then=Value('liked')),
                When(likes__user=request.user.profile, likes__is_like=False, then=Value('disliked')),
                default=Value(None),
                output_field=CharField()  # Changed from models.CharField() to CharField()
            )
        ).order_by('-timestamp')
        
        # Prepare comments data for JSON response
        comments_data = []
        for comment in comments:
            profile_image_url = comment.user.image.url if comment.user.image else None
            comments_data.append({
                'id': comment.id,
                'user_username': comment.user.user.username,
                'user_profile_image': request.build_absolute_uri(profile_image_url) if profile_image_url else None,
                'text': comment.text,
                'timestamp': comment.timestamp.isoformat(),
                'like_count': comment.like_count,
                'dislike_count': comment.dislike_count,
                'reply_count': comment.reply_count,
                'user_like_status': comment.user_like_status,
                'is_reply': False,  # This is a top-level comment
            })
        
        return JsonResponse({'comments': comments_data})
    except Campaign.DoesNotExist:
        return JsonResponse({'error': 'Campaign not found'}, status=404)

@login_required
def post_comment(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user.profile
            
            campaign_id = request.POST.get('campaign_id')
            parent_comment_id = request.POST.get('parent_comment_id')
            
            try:
                campaign = Campaign.objects.get(pk=campaign_id)
                comment.campaign = campaign
                
                if parent_comment_id:
                    parent_comment = Comment.objects.get(pk=parent_comment_id)
                    comment.parent_comment = parent_comment
                
                comment.save()
                
                # Return the new comment data
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'user_username': comment.user.user.username,
                        'user_profile_image': comment.user.image.url if comment.user.image else None,
                        'text': comment.text,
                        'timestamp': comment.timestamp.isoformat(),
                        'like_count': 0,
                        'dislike_count': 0,
                        'reply_count': 0,
                        'user_like_status': None,
                        'is_reply': parent_comment_id is not None,
                    }
                })
            except (Campaign.DoesNotExist, Comment.DoesNotExist):
                return JsonResponse({'error': 'Campaign or parent comment not found'}, status=404)
        else:
            return JsonResponse({'error': 'Invalid form data', 'details': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@require_POST
def like_dislike_comment(request):
    comment_id = request.POST.get('comment_id')
    action = request.POST.get('action')  # 'like', 'dislike', or 'remove'
    
    if not comment_id or not action:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        comment = Comment.objects.get(pk=comment_id)
        profile = request.user.profile
        
        # Check if user already liked/disliked this comment
        try:
            like = CommentLike.objects.get(user=profile, comment=comment)
            
            if action == 'remove' or (action == 'like' and like.is_like) or (action == 'dislike' and not like.is_like):
                # Remove the like/dislike
                like.delete()
                return JsonResponse({
                    'success': True, 
                    'action': 'removed',
                    'like_count': comment.likes.filter(is_like=True).count(),
                    'dislike_count': comment.likes.filter(is_like=False).count()
                })
            else:
                # Update existing like/dislike
                like.is_like = action == 'like'
                like.save()
                return JsonResponse({
                    'success': True, 
                    'action': 'updated',
                    'like_count': comment.likes.filter(is_like=True).count(),
                    'dislike_count': comment.likes.filter(is_like=False).count()
                })
        except CommentLike.DoesNotExist:
            if action in ['like', 'dislike']:
                # Create new like/dislike
                CommentLike.objects.create(
                    user=profile,
                    comment=comment,
                    is_like=(action == 'like')
                )
                return JsonResponse({
                    'success': True, 
                    'action': 'added',
                    'like_count': comment.likes.filter(is_like=True).count(),
                    'dislike_count': comment.likes.filter(is_like=False).count()
                })
            else:
                return JsonResponse({'error': 'Invalid action for new interaction'}, status=400)
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)

from django.db.models import Q, Count

@login_required
def get_replies(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id)
        replies = comment.replies.annotate(
    like_count=Count('likes', filter=Q(likes__is_like=True)),
    dislike_count=Count('likes', filter=Q(likes__is_like=False)),
    user_like_status=Case(
        When(likes__user=request.user.profile, likes__is_like=True, then=Value('liked')),
        When(likes__user=request.user.profile, likes__is_like=False, then=Value('disliked')),
        default=Value(None),
        output_field=CharField()
    )
).order_by('timestamp')


        
        replies_data = []
        for reply in replies:
            profile_image_url = reply.user.image.url if reply.user.image else None
            replies_data.append({
                'id': reply.id,
                'user_username': reply.user.user.username,
                'user_profile_image': request.build_absolute_uri(profile_image_url) if profile_image_url else None,
                'text': reply.text,
                'timestamp': reply.timestamp.isoformat(),
                'like_count': reply.like_count,
                'dislike_count': reply.dislike_count,
                'user_like_status': reply.user_like_status,
                'is_reply': True,
            })
        
        return JsonResponse({'replies': replies_data})
    except Comment.DoesNotExist:
        return JsonResponse({'error': 'Comment not found'}, status=404)










@login_required
def home(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign_id = request.GET.get('campaign_id')
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    if campaign_id:
        campaign = get_object_or_404(Campaign, pk=campaign_id)
    else:
        campaign = Campaign.objects.first()  # Default campaign
    
    user = request.user
    already_loved = campaign and user != campaign.user and Love.objects.filter(campaign=campaign, user=user).exists()

    # Get campaigns, annotate whether the user marked them as "not interested"
    campaigns = Campaign.objects.annotate(
        is_not_interested=Case(
            When(not_interested_by__user=user_profile, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).filter(is_not_interested=False, visibility='public').select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        campaigns = campaigns.filter(category=category_filter)

   
    campaigns = campaigns.order_by('-timestamp')

    following_users = request.user.following.values_list('followed', flat=True)
    followed_campaigns = campaigns.filter(user__user__in=following_users)
    own_campaigns = campaigns.filter(user=user_profile)
    campaigns_to_display = followed_campaigns | own_campaigns

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')


    # ✅ Apply category filter before slicing
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]  # Show top 10 trending campaigns

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check
    ).exclude(id__in=NotInterested.objects.filter(user=user_profile).values_list('campaign_id', flat=True)).order_by('-timestamp')

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()
    categories = Campaign.objects.values_list('category', flat=True).distinct()  # Fetch unique categories

    # Get suggested users with followers count
    current_user_following_ids = set(request.user.following.values_list('followed_id', flat=True))
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=current_user_following_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]
# Annotate profiles with campaign count and total raised
    
# Collect all user-campaign engagement pairs
    engaged_users = set()

# Collect engagement user-campaign pairs
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')

    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')

    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

# Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

# Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

# Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
            'user': profile.user,
            'image': profile.image,
            'campaign_count': len(campaign_set),
        })
        except Profile.DoesNotExist:
            continue

# Sort contributors by campaign_count descending
        top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]  # Top 5
    return render(request, 'main/home.html', {
        'ads': ads,
        'public_campaigns': campaigns_to_display if campaigns_to_display.exists() else trending_campaigns,
        'campaign': Campaign.objects.last(),
        'already_loved': already_loved,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'categories': categories,  # Pass categories to template
        'selected_category': category_filter,  # Pass selected category to retain state
        'trending_campaigns': trending_campaigns,
        'suggested_users': suggested_users,
        'top_contributors': top_contributors,
        
    })








@login_required
def face(request):
    form = SubscriptionForm()
    following_users = [follow.followed for follow in request.user.following.all()]
    user_profile = get_object_or_404(Profile, user=request.user)
    category_filter = request.GET.get('category', '')  # Get category filter from request

    campaign = Campaign.objects.last()

    if user_profile.last_campaign_check is None:
        user_profile.last_campaign_check = timezone.now()
        user_profile.save()

    new_private_campaigns_count = Campaign.objects.filter(
        visibility='private',
        timestamp__gt=user_profile.last_campaign_check
    ).count()

    # Debugging output
    print(f"Last Campaign Check: {user_profile.last_campaign_check}")
    print(f"New Private Campaigns Count: {new_private_campaigns_count}")

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')

    # ✅ Apply category filter before slicing
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]  # Show top 10 trending campaigns

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]  # Top 5

    ads = NativeAd.objects.all()
    categories = Campaign.objects.values_list('category', flat=True).distinct()  # Fetch unique categories

    return render(request, 'main/face.html', {
        'ads': ads,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'form': form,
        'new_private_campaigns_count': new_private_campaigns_count,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,  # Pass categories to template
        'selected_category': category_filter,  # Pass selected category to retain state
    })









@login_required
def campaign_comments(request, campaign_id):
    # Retrieve campaign object
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    user_profile = get_object_or_404(Profile, user=request.user)
    
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        return HttpResponseForbidden("Campaign does not exist.")

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user.profile
            comment.campaign_id = campaign_id
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = CommentForm()

    comments = Comment.objects.filter(campaign_id=campaign_id).order_by('-timestamp')
    
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    # Fetch unread messages for the user
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(
        chat__in=user_chats
    ).exclude(sender=request.user).count()

    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'campaign': campaign,
        'comments': comments,
        'form': form,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/campaign_comments.html', context)


def campaign_support(request, campaign_id):
    # Get basic campaign and user data
    user_profile = None
    following_user_ids = []
    
    if request.user.is_authenticated:
        # Get following user IDs using the improved pattern
        current_user_following = request.user.following.all()
        following_user_ids = [follow.followed_id for follow in current_user_following]
        user_profile = get_object_or_404(Profile, user=request.user)
        # Update last campaign check time
        user_profile.last_campaign_check = timezone.now()
        user_profile.save()

    support_campaign = SupportCampaign.objects.filter(campaign_id=campaign_id).first()
    
    # Notifications and messages
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False) if request.user.is_authenticated else []
    
    # New campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check if user_profile else timezone.now()
    ) if request.user.is_authenticated else []

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Suggested users (only for authenticated users)
    suggested_users = []
    if request.user.is_authenticated:
        all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
        
        for profile in all_profiles:
            similarity_score = calculate_similarity(user_profile, profile)
            if similarity_score >= 0.5:
                followers_count = Follow.objects.filter(followed=profile.user).count()
                suggested_users.append({
                    'user': profile.user,
                    'followers_count': followers_count
                })
        suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'support_campaign': support_campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/campaign_support.html', context)


@login_required
def recreate_campaign(request, campaign_id):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    categories = Campaign.CATEGORY_CHOICES
    existing_campaign = get_object_or_404(Campaign, pk=campaign_id)

    # Handle form submission
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=existing_campaign)
        if form.is_valid():
            form.save()
            return redirect('success_page')  # Update with your success URL
    else:
        form = CampaignForm(instance=existing_campaign)

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Notifications and follows
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids,
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'form': form,
        'categories': categories,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'existing_campaign': existing_campaign,
    }
    
    return render(request, 'main/recreatecampaign_form.html', context)


def success_page(request):
    return render(request, 'main/success.html')




@login_required
def create_campaign(request):
    following_users = [follow.followed for follow in request.user.following.all()]
    user_profile = get_object_or_404(Profile, user=request.user)
    categories = Campaign.CATEGORY_CHOICES

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user.profile
            campaign.save()
            messages.success(request, 'Campaign created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'There were errors in your form. Please correct them below.')
    else:
        form = CampaignForm()

    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]


    ads = NativeAd.objects.all()

    context = {
        'ads': ads,
        'form': form,
        'categories': categories,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/campaign_form.html', context)

def poster_canva(request):
    return render(request, 'main/poster_canva.html', {
        'username': request.user.username
    })



def video_canva(request):
    return render(request, 'main/video_canva.html', {
        'username': request.user.username
    })



@login_required
def home(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign_id = request.GET.get('campaign_id')
    category_filter = request.GET.get('category', '')
    
    if campaign_id:
        campaign = get_object_or_404(Campaign, pk=campaign_id)
    else:
        campaign = Campaign.objects.first()

    user = request.user
    already_loved = campaign and user != campaign.user and Love.objects.filter(campaign=campaign, user=user).exists()

    # Get campaigns, annotate whether the user marked them as "not interested"
    campaigns = Campaign.objects.annotate(
        is_not_interested=Case(
            When(not_interested_by__user=user_profile, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).filter(is_not_interested=False, visibility='public').select_related('campaignfund')

    if category_filter:
        campaigns = campaigns.filter(category=category_filter)

    campaigns = campaigns.order_by('-timestamp')

    # Get users the current user is following
    following_users = request.user.following.values_list('followed', flat=True)
    followed_campaigns = campaigns.filter(user__user__in=following_users)
    own_campaigns = campaigns.filter(user=user_profile)
    campaigns_to_display = followed_campaigns | own_campaigns

    # Trending campaigns
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')

    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()
    
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    ).exclude(id__in=NotInterested.objects.filter(user=user_profile).values_list('campaign_id', flat=True)).order_by('-timestamp')

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    ads = NativeAd.objects.all()
    categories = Campaign.objects.values_list('category', flat=True).distinct()

    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    return render(request, 'main/home.html', {
        'ads': ads,
        'public_campaigns': campaigns_to_display if campaigns_to_display.exists() else trending_campaigns,
        'campaign': Campaign.objects.last(),
        'already_loved': already_loved,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'categories': categories,
        'selected_category': category_filter,
        'trending_campaigns': trending_campaigns,
        'suggested_users': suggested_users,
        'top_contributors': top_contributors,
    })





@login_required
def face(request):
    form = SubscriptionForm()
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request

    campaign = Campaign.objects.last()
    user_profile = None

    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)

        if user_profile.last_campaign_check is None:
            user_profile.last_campaign_check = timezone.now()
            user_profile.save()

        new_private_campaigns_count = Campaign.objects.filter(
            visibility='private',
            timestamp__gt=user_profile.last_campaign_check
        ).count()

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()

    # Get suggested users with followers count
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')

    # ✅ Apply category filter before slicing
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]  # Show top 10 trending campaigns

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]  # Top 5

    ads = NativeAd.objects.all()
    categories = Campaign.objects.values_list('category', flat=True).distinct()  # Fetch unique categories

    return render(request, 'main/face.html', {
        'ads': ads,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'form': form,
        'new_private_campaigns_count': new_private_campaigns_count,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,  # Pass categories to template
        'selected_category': category_filter,  # Pass selected category to retain state
    })



def follower_list(request, username):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    user = User.objects.get(username=username)
    followers = Follow.objects.filter(followed=user)
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows (using consistent following_user_ids)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()  
    
    # Get suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'user': user,
        'followers': followers,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }

    return render(request, 'main/follower_list.html', context)

def following_list(request, username):
    # Get following user IDs using the improved pattern
    current_user_following = request.user.following.all()
    following_user_ids = [follow.followed_id for follow in current_user_following]
    
    user_profile = get_object_or_404(Profile, user=request.user)
    user = User.objects.get(username=username)
    following = Follow.objects.filter(follower=user)
    category_filter = request.GET.get('category', '')  # Get category filter from request
    
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Check if there are new campaigns from follows (using consistent following_user_ids)
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__id__in=following_user_ids, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()
    
    # Get suggested users with improved logic
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            # Get followers count for each suggested user
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1)\
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
        brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'user': user,
        'following': following,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }

    return render(request, 'main/following_list.html', context)







@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if request.user == user_to_follow:
        messages.error(request, "You cannot follow yourself.")
    else:
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
        if created:
            messages.success(request, f"You are now following {username}.")
        else:
            messages.info(request, f"You are already following {username}.")
    return redirect('profile_view', username=username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, followed=user_to_unfollow).delete()
    messages.success(request, f"You have unfollowed {username}.")
    return redirect('profile_view', username=username)







@login_required
def profile_edit(request, username):
    following_users = [follow.followed for follow in request.user.following.all()]
    category_filter = request.GET.get('category', '')  # Get category filter from request
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_profile = get_object_or_404(Profile, user=request.user)
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    new_campaigns_from_follows = Campaign.objects.filter(
        user__user__in=following_users, 
        visibility='public', 
        timestamp__gt=user_profile.last_campaign_check
    )
    
    ads = NativeAd.objects.all()
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('home')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    # Improved suggested users logic
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to 2 suggested users
    suggested_users = suggested_users[:2]

    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund')

    # Apply category filter if provided
    if category_filter:
        trending_campaigns = trending_campaigns.filter(category=category_filter)

    trending_campaigns = trending_campaigns.order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    categories = Campaign.objects.values_list('category', flat=True).distinct()

    context = {
        'ads': ads,
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'username': username,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
        'categories': categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'main/edit_profile.html', context)






from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile, Follow

@login_required
def profile_view(request, username):
    # Get the user's profile (username will come without @ due to URL pattern)
    user_profile = get_object_or_404(Profile, user__username=username)
    
    # Check if the logged-in user is following this profile
    following_profile = Follow.objects.filter(follower=request.user, followed=user_profile.user).exists()
    
    # Calculate followers and following counts
    followers_count = Follow.objects.filter(followed=user_profile.user).count()
    following_count = Follow.objects.filter(follower=user_profile.user).count()
    
    # Get public campaigns
    public_campaigns = user_profile.user_campaigns.filter(visibility='public').order_by('-timestamp')
    public_campaigns_count = public_campaigns.count()
    
    # Filter campaigns where the user qualifies as a changemaker
    changemaker_campaigns = [campaign for campaign in public_campaigns if campaign.is_changemaker]
    
    # Determine the most appropriate campaign
    most_appropriate_campaign = None
    if changemaker_campaigns:
        first_campaign = min(changemaker_campaigns, key=lambda campaign: campaign.timestamp)
        most_impactful_campaign = max(changemaker_campaigns, key=lambda campaign: campaign.love_count)
        
        if most_impactful_campaign.love_count == first_campaign.love_count:
            most_appropriate_campaign = max(changemaker_campaigns, key=lambda campaign: campaign.timestamp)
        else:
            most_appropriate_campaign = most_impactful_campaign
    
    category_display = most_appropriate_campaign.get_category_display() if most_appropriate_campaign else None
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    # 🔥 Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    engaged_users = set()
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)

    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    # Get suggested users with followers count (using improved logic)
    current_user_following = request.user.following.all()  # Get all Follow objects
    following_user_ids = [follow.followed_id for follow in current_user_following]  # Extract user IDs
    
    # Exclude current user and already followed users
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=following_user_ids)
    
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })

    # Limit to only 2 suggested users
    suggested_users = suggested_users[:2]

    ads = NativeAd.objects.all()

    context = {
        'user_profile': user_profile,
        'following_profile': following_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'public_campaigns': public_campaigns,
        'public_campaigns_count': public_campaigns_count,
        'changemaker_category': category_display,
        'ads': ads,
        'unread_notifications': unread_notifications,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'main/user_profile.html', context)



def search_profile_results(request):
    if 'search_query' in request.GET:
        form = ProfileSearchForm(request.GET)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            results = Profile.objects.filter(user__username__icontains=search_query)
            return render(request, 'main/search_profile_results.html', {'search_results': results, 'query': search_query})
    return render(request, 'main/search_profile_results.html', {'search_results': [], 'query': ''})







#marketing

from .models import Blog

def blog_list(request):
    blogs = Blog.objects.filter(is_published=True).order_by('-created_at')  # Show latest first
    return render(request, 'marketing/blog_list.html', {'blogs': blogs})    



def blog_detail(request, slug):
    blog_post = get_object_or_404(Blog, slug=slug, is_published=True)
    return render(request, 'marketing/blog_detail.html', {'blog_post': blog_post})


from .models import CampaignStory

def campaign_story_list(request):
    stories = CampaignStory.objects.all().order_by('-created_at')  # Order by creation date in descending order
    return render(request, 'marketing/story_list.html', {'stories': stories})


def campaign_story_detail(request, slug):
    story = get_object_or_404(CampaignStory, slug=slug)
    return render(request, 'marketing/story_detail.html', {'story': story})



def success_stories(request):
    return render(request, 'marketing/success_stories.html')


def testimonial(request):
    return render(request, 'marketing/testimonial.html')




from .models import FAQ
# views.py
def faq_view(request):
    categories = []
    for choice in FAQ.CATEGORY_CHOICES:
        faqs = FAQ.objects.filter(category=choice[0])
        if faqs.exists():  # Only include categories with FAQs
            categories.append({
                'name': choice[1],
                'code': choice[0],
                'faqs': faqs
            })
    
    return render(request, 'marketing/faq.html', {'categories': categories})

def hiw(request):
    return render(request, 'marketing/hiw.html')

def aboutus(request):
    return render(request, 'marketing/aboutus.html')


def fund(request):
    return render(request, 'marketing/fund.html')


def geno(request):
    return render(request, 'marketing/geno.html')






import paypalrestsdk
from django.conf import settings
from django.shortcuts import redirect

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # Sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})





def donate(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    fund, created = CampaignFund.objects.get_or_create(
        campaign=campaign, 
        defaults={'target_amount': 0.00, 'paypal_email': 'default_email@example.com'}
    )
    target_reached = fund.progress_percentage() >= 100

    if request.method == 'POST':
        donation_form = DonationForm(request.POST)
        fund_form = CampaignFundForm(request.POST, instance=fund)

        if 'donate' in request.POST and not target_reached:
            if donation_form.is_valid():
                donation_amount = request.POST.get('amount')
                payment = paypalrestsdk.Payment({
                    "intent": "sale",
                    "payer": {"payment_method": "paypal"},
                    "redirect_urls": {
                        "return_url": request.build_absolute_uri(reverse('payment_success', args=[campaign_id])),
                        "cancel_url": request.build_absolute_uri(reverse('payment_cancel')),
                    },
                    "transactions": [{
                        "item_list": {"items": [{
                            "name": f"Donation for {campaign.title}",
                            "sku": "donation",
                            "price": donation_amount,
                            "currency": "USD",
                            "quantity": 1
                        }]},
                        "amount": {"total": donation_amount, "currency": "USD"},
                        "description": f"Donation for {campaign.title}",
                        "payee": {"email": fund.paypal_email}
                    }]
                })

                if payment.create():
                    for link in payment.links:
                        if link.rel == "approval_url":
                            return redirect(link.href)
                else:
                    messages.error(request, 'Error creating PayPal payment.')

        elif 'update_campaign' in request.POST:
            if fund_form.is_valid():
                fund_form.save()
                messages.success(request, 'Donation info updated successfully.')
            else:
                messages.error(request, 'Error updating donation info.')
    else:
        donation_form = DonationForm()
        fund_form = CampaignFundForm(instance=fund)

    # User data and following
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = request.user.following.values_list('followed', flat=True)
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    ads = NativeAd.objects.all()

    # Suggested users
    current_user_following = user_profile.following.all()
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)
    suggested_users = []
    
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:
            followers_count = Follow.objects.filter(followed=profile.user).count()
            suggested_users.append({
                'user': profile.user,
                'followers_count': followers_count
            })
    suggested_users = suggested_users[:2]

    # Trending campaigns (Only those with at least 1 love)
    trending_campaigns = Campaign.objects.filter(visibility='public') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .select_related('campaignfund') \
        .order_by('-love_count_annotated')[:10]

    # Top Contributors logic
    donation_pairs = Donation.objects.values_list('donor__id', 'campaign_id')
    love_pairs = Love.objects.values_list('user_id', 'campaign_id')
    comment_pairs = Comment.objects.values_list('user_id', 'campaign_id')
    view_pairs = CampaignView.objects.values_list('user_id', 'campaign_id')
    brainstorm_pairs = Brainstorming.objects.values_list('supporter_id', 'campaign_id')
    activity_love_pairs = ActivityLove.objects.values_list('user_id', 'activity__campaign_id')
    activity_comment_pairs = ActivityComment.objects.values_list('user_id', 'activity__campaign_id')

    # Combine all engagement pairs
    all_pairs = chain(donation_pairs, love_pairs, comment_pairs, view_pairs,
                     brainstorm_pairs, activity_love_pairs, activity_comment_pairs)

    # Count number of unique campaigns each user engaged with
    user_campaign_map = defaultdict(set)
    for user_id, campaign_id in all_pairs:
        user_campaign_map[user_id].add(campaign_id)

    # Build a list of contributors with their campaign engagement count
    contributor_data = []
    for user_id, campaign_set in user_campaign_map.items():
        try:
            profile = Profile.objects.get(user__id=user_id)
            contributor_data.append({
                'user': profile.user,
                'image': profile.image,
                'campaign_count': len(campaign_set),
            })
        except Profile.DoesNotExist:
            continue

    # Sort contributors by campaign_count descending
    top_contributors = sorted(contributor_data, key=lambda x: x['campaign_count'], reverse=True)[:5]

    context = {
        'campaign': campaign,
        'form': donation_form,
        'fund_form': fund_form,
        'fund': fund,
        'target_reached': target_reached,
        'user_profile': user_profile,
        'ads': ads,
        'suggested_users': suggested_users,
        'trending_campaigns': trending_campaigns,
        'top_contributors': top_contributors,
    }
    
    return render(request, 'revenue/donation.html', context)


from django.urls import reverse
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
import paypalrestsdk

@login_required
def payment_success(request, campaign_id):
    # Extract PayPal payment information
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    # Check if this payment has already been processed
    if Donation.objects.filter(transaction_id=payment_id).exists():
        messages.warning(request, 'This payment has already been processed.')
        return redirect('donate', campaign_id=campaign_id)

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Payment was successful, update campaign fund
        campaign = get_object_or_404(Campaign, id=campaign_id)
        fund = CampaignFund.objects.get(campaign=campaign)
        amount = Decimal(payment.transactions[0].amount.total)

# Calculate 5% commission fee
        commission_percentage = Decimal('0.05')  # 5%
        commission_fee = (amount * commission_percentage).quantize(Decimal('0.01'))  # rounding to cents

        net_amount = amount - commission_fee

# Update the amount raised
        fund.amount_raised += net_amount
        fund.save()
        # Create the donation record (with transaction ID to avoid duplicates)
        Donation.objects.create(
            campaign=campaign,
            amount=net_amount,  # Store the net amount after deductions
            donor_name=request.user.username,  # or anonymous if you allow it
            transaction_id=payment_id  # Store the PayPal payment ID
        )

        # Send commission to your PayPal account
        payout = paypalrestsdk.Payout({
            "sender_batch_header": {
                "sender_batch_id": str(payment_id),
                "email_subject": "Commission Payment"
            },
            "items": [{
                "recipient_type": "EMAIL",
                "amount": {
                    "value": str(commission_fee),
                    "currency": "USD"
                },
                "receiver":settings.PAYPAL_PLATFORM_EMAIL,  # Your PayPal email
                "note": f"Commission for donation {payment_id}",
                "sender_item_id": str(payment_id)
            }]
        })

        # Create payout with asynchronous mode
        if payout.create(sync_mode=False):
            messages.success(request, 'Thank you for your donation! A commission has been processed.')
        else:
            messages.error(request, f'Failed to process commission. Error: {payout.error}')

        # Calculate the updated progress percentage
        if fund.target_amount > 0:
            fund.progress_percentage = (fund.amount_raised / fund.target_amount) * 100
        else:
            fund.progress_percentage = 100  # Avoid division by zero

        fund.save()  # Save the updated progress percentage

        return redirect('donate', campaign_id=campaign_id)

    # If payment execution failed
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('donate', campaign_id=campaign_id)


@login_required
def payment_cancel(request):
    messages.warning(request, 'Payment was cancelled.')
    return redirect('donate')






