
import paypalrestsdk

import time  # Import the time module

import logging
import json

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
    User, Love, CampaignView, Chat, Notification,Message, Donation
)
from .forms import   BrainstormingForm
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
from .forms import DonationForm
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

from django.core.files.uploadedfile import SimpleUploadedFile
from mimetypes import guess_type
from .models import  Report
from .forms import ReportForm,NotInterestedForm
from .models import  NotInterested
from django.contrib.admin.views.decorators import staff_member_required
from .models import QuranVerse,Surah
from .models import Adhkar
from .models import Hadith
from .models import PlatformFund
from .forms import SubscriptionForm
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
    return render(request, 'affiliate/library_affiliates.html', {'ads':ads,'libraries': libraries,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows})

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
    return render(request, 'affiliate/news_affiliates.html', {'ads':ads,'news_sources': news_sources,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows})






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
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    platformfunds = PlatformFund.objects.all()
    ads = NativeAd.objects.all()  
    return render(request, 'revenue/platformfund.html', {'ads':ads,'platformfunds': platformfunds,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows})




def hadith_list(request):
    hadiths = Hadith.objects.all()
    return render(request, 'main/hadith_list.html', {'hadiths': hadiths})


def hadith_detail(request, hadith_id):
    # Retrieve the specific Hadith object or return a 404 error if not found
    hadith = get_object_or_404(Hadith, pk=hadith_id)
    return render(request, 'main/hadith_detail.html', {'hadith': hadith})


def adhkar_list(request):
    adhkars = Adhkar.objects.all()
    return render(request, 'main/adhkar_list.html', {'adhkars': adhkars})

def adhkar_detail(request, adhkar_id):
    adhkar = get_object_or_404(Adhkar, id=adhkar_id)
    return render(request, 'main/adhkar_detail.html', {'adhkar': adhkar})



@login_required
def quran_view(request):
    surahs = Surah.objects.all()
    quran_verses = QuranVerse.objects.all()

    return render(request, 'main/quran.html', {
        'surahs': surahs,
        'quran_verses': quran_verses
    })







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
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)
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
        # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/report_campaign.html', {'ads':ads,'form': form, 'campaign': campaign,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows})








def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        # Save the image to the desired location or process it as needed
        # Example: activity.image = image_file; activity.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def product_manage(request, campaign_id=None, product_id=None):
    campaign = None
    product = None

    if campaign_id:
        campaign = get_object_or_404(Campaign, pk=campaign_id)

    if product_id:
        product = get_object_or_404(CampaignProduct, pk=product_id)

    if request.method == 'POST':
        form = CampaignProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.campaign = campaign
            product.save()
            # Redirect back to product_manage view
            if campaign:
                return redirect('product_manage', campaign_id=campaign.id)
            else:
                return redirect('product_manage')
    else:
        form = CampaignProductForm(instance=product)
    
    products = CampaignProduct.objects.filter(campaign=campaign) if campaign else None
        # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/product_manage.html', {'ads':ads,'form': form, 'product': product, 'campaign': campaign, 'products': products,'unread_notifications':unread_notifications,'user_profile': user_profile,'new_campaigns_from_follows': new_campaigns_from_follows})

def love_activity(request, activity_id):
    if request.method == 'POST' and request.user.is_authenticated:
        activity = Activity.objects.get(id=activity_id)
        # Check if the user has already loved this activity
        if not ActivityLove.objects.filter(activity=activity, user=request.user).exists():
            # Create a new love for this activity by the user
            ActivityLove.objects.create(activity=activity, user=request.user)
        # Get updated love count for the activity
        love_count = activity.loves.count()
        return JsonResponse({'love_count': love_count})
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)











def activity_detail(request, activity_id):

    user_profile = get_object_or_404(Profile, user=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # You can add any additional context data here if needed
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/activity_detail.html', {'ads':ads,'activity': activity,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})



def add_activity_comment(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save() 
    ads = NativeAd.objects.all()     
    if request.method == 'POST':
        form = ActivityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.activity = activity
            comment.user = request.user  # Assuming you have user authentication
            comment.save()
            return JsonResponse({
                'success': True, 
                'content': comment.content, 
                'username': comment.user.username, 
                'timestamp': comment.timestamp,
                'profile_image_url': comment.user.profile.image.url  # Include profile image URL
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        comments = activity.activitycomment_set.all().order_by('-timestamp')  # Retrieve comments for the activity, ordered by timestamp descending
        form = ActivityCommentForm()
        return render(request, 'main/add_activity_comment.html', {
            'activity': activity, 
            'comments': comments, 
            'form': form,
            'user_profile': user_profile,
            'unread_notifications': unread_notifications,
            'new_campaigns_from_follows': new_campaigns_from_follows,
            'ads':ads,
        })




@login_required
def suggest(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    current_user_following = user_profile.following.all()
    suggested_users = []

    # Fetch all profiles except the current user's profile and those the current user is already following
    all_profiles = Profile.objects.exclude(user=request.user).exclude(user__in=current_user_following)

    # Calculate similarity score for each profile and include those with a score >= 0.5
    for profile in all_profiles:
        similarity_score = calculate_similarity(user_profile, profile)
        if similarity_score >= 0.5:  # Adjust this threshold as needed
            suggested_users.append(profile.user)

    # Remove profiles that the current user is already following
    suggested_users = [user for user in suggested_users if user not in following_users]

    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/suggest.html', {'ads':ads,'suggested_users': suggested_users, 'user_profile': user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})














def affiliate_links(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    affiliate_links = AffiliateLink.objects.all()
    ads = NativeAd.objects.all()  
    return render(request, 'revenue/affiliate_links.html', {'ads':ads,'affiliate_links': affiliate_links,'user_profile': user_profile,
                                               'unread_notifications': unread_notifications,
    
                                               'new_campaigns_from_follows': new_campaigns_from_follows})




def donate(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Retrieve donations for the current campaign
    donations = Donation.objects.filter(campaign=campaign)
    ads = NativeAd.objects.all()  
    if request.method == 'POST':
        # Handle donation deletion
        if 'delete_donation' in request.POST:
            donation_id = request.POST.get('delete_donation')
            donation = get_object_or_404(Donation, id=donation_id)
            if donation.user == request.user:  # Check if the user owns the donation
                donation.delete()
                return redirect('donate', campaign_id=campaign_id)
        
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.user = request.user
            donation.campaign = campaign
            donation.save()
            return redirect('donate', campaign_id=campaign_id)  # Redirect to a thank you page or any other page you desire
    else:
        form = DonationForm()
    
    context = {
        'ads':ads,
        'form': form,
        'campaign': campaign,
        'donations': donations, 
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,  # Pass donations to the template context
    }
    return render(request, 'revenue/donation.html', context)





@login_required
def update_visibility(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
        # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
                    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        # Get all support campaigns associated with the specified campaign ID
        try:
            campaigns = SupportCampaign.objects.filter(campaign_id=campaign_id)
        except ObjectDoesNotExist:
            return HttpResponseServerError("Campaign not found")
        except MultipleObjectsReturned:
            # Handle the situation where multiple campaigns are found
            return HttpResponseServerError("Multiple campaigns found for the same ID")
        
        # Update visibility settings for each support campaign
        for campaign in campaigns:
            campaign.donate_monetary_visible = request.POST.get('donate_monetary_visible', False) == 'on'
            campaign.share_social_media_visible = request.POST.get('share_social_media_visible', False) == 'on'
          
            campaign.provide_resource_visible = request.POST.get('provide_resource_visible', False) == 'on'
            campaign.brainstorm_idea_visible = request.POST.get('brainstorm_idea_visible', False) == 'on'
            campaign.campaign_product_visible = request.POST.get('campaign_product_visible', False) == 'on'
         
            campaign.save()
        
        return redirect('support', campaign_id=campaign_id)
    else:
        try:
            # Get the campaign for which visibility settings are being updated
            campaign = Campaign.objects.get(pk=campaign_id)
        except ObjectDoesNotExist:
            return HttpResponseServerError("Campaign not found")
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/update_visibility.html', {'ads':ads,'campaign': campaign,
            'user_profile':user_profile,
            'unread_notifications':unread_notifications,
            'new_campaigns_from_follows':new_campaigns_from_follows
            })


@login_required
def support(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    campaign = Campaign.objects.get(id=campaign_id)
        # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    # Retrieve the SupportCampaign object for the current user and campaign
    try:
        support_campaign = SupportCampaign.objects.get(user=request.user, campaign=campaign)
    except SupportCampaign.DoesNotExist:
        # If the user hasn't supported this campaign yet, create a new SupportCampaign object
        support_campaign = SupportCampaign.objects.create(user=request.user, campaign=campaign)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)
    products = CampaignProduct.objects.filter(campaign=campaign) if campaign else None
    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Pass the support_campaign object to the template
    return render(request, 'main/support.html', {'ads':ads,'campaign': campaign, 'support_campaign': support_campaign, 'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows,'products':products})


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
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    campaign = Campaign.objects.get(id=campaign_id)
    user_profile = get_object_or_404(Profile, user=request.user)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    if request.method == 'POST':
        form = BrainstormingForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.supporter = request.user
            idea.campaign = campaign
            idea.save()
            # Retrieve all ideas for the current campaign after saving the new idea
            ideas_for_campaign = Brainstorming.objects.filter(campaign=campaign).order_by('-pk')  # Order by creation timestamp in descending order
            return render(request, 'main/brainstorm.html', {'ads':ads,'form': form, 'ideas_for_campaign': ideas_for_campaign,'user_profile':user_profile, 'campaign': campaign,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})
    else:
        form = BrainstormingForm()
    
    # Retrieve all ideas for the current campaign before displaying the form
    ideas_for_campaign = Brainstorming.objects.filter(campaign=campaign).order_by('-pk')  # Order by creation timestamp in descending order
    return render(request, 'main/brainstorm.html', {'form': form, 'ideas_for_campaign': ideas_for_campaign,'user_profile':user_profile, 'campaign': campaign,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})




@login_required
def donate_monetary(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following

    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = get_object_or_404(Campaign, id=campaign_id)
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/donate_monetary.html', {'ads':ads,'campaign': campaign,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})






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
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    query = request.GET.get('search_query')
    
    # Initialize empty querysets for campaigns, profiles, Quran verses, and Hadiths
    campaigns = Campaign.objects.none()
    profiles = Profile.objects.none()
    quran_verses = QuranVerse.objects.none()
    adhkar = Adhkar.objects.none()  # Initialize queryset for Adhkar
    hadiths = Hadith.objects.none()  # Initialize queryset for Hadiths
    
    if query:
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
            Q(surah__name__icontains=query)  # Filter based on the name of the Surah
        )

        adhkar = Adhkar.objects.filter(
            Q(type__icontains=query) |  # Filter based on the 'type' field
            Q(text__icontains=query) |
            Q(translation__icontains=query) |
            Q(reference__icontains=query)
        )

        # Search for Hadiths based on the query
        hadiths = Hadith.objects.filter(
            Q(narrator__icontains=query) |
            Q(text__icontains=query) |
            Q(reference__icontains=query) |
            Q(authenticity__icontains=query)
        )
    
    # Retrieve notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    # Mark notifications as viewed
    unread_notifications = notifications.filter(viewed=False)
    unread_notifications.update(viewed=True)
    # Count unread notifications
    unread_count = unread_notifications.count()
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()    
    ads = NativeAd.objects.all()  
    return render(request, 'main/search_results.html', {
        'ads':ads,
        'campaigns': campaigns,
        'profiles': profiles,
        'quran_verses': quran_verses,
        'adhkar': adhkar,
        'hadiths': hadiths,  # Pass hadiths queryset to the template
        'user_profile': user_profile,
        'unread_count': unread_count,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows
    })



@login_required
def notification_list(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    # Retrieve notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    # Mark notifications as viewed
    unread_notifications = notifications.filter(viewed=False)
    unread_notifications.update(viewed=True)

    # Count unread notifications
    unread_count = unread_notifications.count()
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    context = {
        'ads':ads,
        'notifications': notifications,
        'user_profile': user_profile,
        'unread_count': unread_count,  # Pass the unread count to the template
        'unread_notifications':unread_notifications,
        'new_campaigns_from_follows':new_campaigns_from_follows
    }
    return render(request, 'main/notification_list.html', context)



@login_required
def create_chat(request):
    following_users = [follow.followed for follow in request.user.following.all()]  
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
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/create_chat.html', {'ads':ads,'form': form,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})



@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    # Get the list of users followed by the current user
    following_users = [follow.followed for follow in request.user.following.all()]
    
    # Get the list of followers of the current user
    followers = [follow.follower for follow in request.user.followers.all()]
    
    # Combine followers and following users into a single set to eliminate duplicates
    combined_users = set(following_users + followers)
    
    # Exclude the current user and users who are already participants in the chat
    user_choices = User.objects.filter(
        pk__in=[user.pk for user in combined_users]
    ).exclude(pk=request.user.pk).exclude(pk__in=[participant.pk for participant in chat.participants.all()])
    
    # Get the user profile and chat
    user_profile = get_object_or_404(Profile, user=request.user)

    
    # Get all messages for the chat ordered by timestamp
    messages = Message.objects.filter(chat=chat).order_by('timestamp')
    
    if request.method == 'POST':
        message_form = MessageForm(request.POST, request.FILES)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.sender = request.user
            message.chat = chat
            message.save()
            return JsonResponse({'status': 'success', 'message': 'Message sent successfully', 'message_id': message.id})
        else:
            return JsonResponse({'status': 'error', 'message': 'Form data is invalid', 'errors': message_form.errors})
    else:
        message_form = MessageForm(initial={'chat': chat})
    
    # Get unread notifications for the current user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    
    # Get new public campaigns from followed users since the last campaign check
    new_campaigns_from_follows = Campaign.objects.filter(
        user__in=[user.pk for user in following_users],
        visibility='public',
        timestamp__gt=user_profile.last_campaign_check
    )
    
    # Update the last campaign check time for the current user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    # Render the chat detail template with the relevant context
    context = {
        'ads':ads,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'user_profile': user_profile,
        'chat': chat,
        'message_form': message_form,
        'messages': messages,
        'user_choices': user_choices
    }
    
    return render(request, 'main/chat_detail.html', context)



@login_required
def user_chats(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    last_chat_check = user_profile.last_chat_check

    user_profile.last_chat_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  

    following_users = [follow.followed for follow in request.user.following.all()]  
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False) 
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    user_chats = Chat.objects.filter(participants=request.user) | Chat.objects.filter(manager=request.user)
    
    for chat in user_chats:
        chat.has_unread_messages = chat.messages.filter(timestamp__gt=last_chat_check).exists()

    return render(request, 'main/user_chats.html', {
        'ads':ads,
        'user_chats': user_chats,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
    })

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




def view_campaign(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    user_profile = None
    already_loved = False

    if request.user.is_authenticated:
        user_profile = request.user.profile

        # Check if the current user has loved the campaign
        already_loved = Love.objects.filter(user=request.user, campaign=campaign).exists()

        if not CampaignView.objects.filter(user=user_profile, campaign=campaign).exists():
            CampaignView.objects.create(user=user_profile, campaign=campaign)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save() 
    ads = NativeAd.objects.all()   
    return render(request, 'main/campaign_detail.html', {'campaign': campaign, 'ads':ads,'user_profile': user_profile, 'already_loved': already_loved,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})






def campaign_detail(request, pk):
    # Retrieve the campaign object using its primary key (pk)
    campaign = get_object_or_404(Campaign, pk=pk)
    form = SubscriptionForm()
    # Pass the campaign object to the template for rendering
    return render(request, 'main/campaign_detail.html', {'campaign': campaign,'form':form})


def thank_you(request):
    
    return render(request, 'main/thank_you.html')









def activity_list(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the campaign object
    campaign = Campaign.objects.get(id=campaign_id)
    
    # Get all activities associated with the campaign
    activities = Activity.objects.filter(campaign=campaign).order_by('-timestamp')
    
    # Fetch comment count for each activity
    for activity in activities:
        activity.comment_count = ActivityComment.objects.filter(activity=activity).count()
    
    # List of image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    # Count the number of activities
    activity_count = activities.count()
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    context = {
    'ads':ads,
        'campaign': campaign, 
        'activities': activities, 
        'image_extensions': image_extensions,
        'user_profile': user_profile,
        'activity_count': activity_count,
        'unread_notifications':unread_notifications,
        'new_campaigns_from_follows':new_campaigns_from_follows
    }
    
    return render(request, 'main/activity_list.html', context)









@login_required
def create_activity(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
            # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    campaign = Campaign.objects.get(id=campaign_id)

    if request.method == 'POST':
        formset = ActivityFormSet(request.POST, request.FILES, instance=campaign)
        if formset.is_valid():
            formset.save()
            return redirect('activity_list',campaign_id=campaign_id)  # Redirect to campaign detail view
    else:
        formset = ActivityFormSet(instance=campaign)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    return render(request, 'main/activity_create.html', {'ads':ads,'formset': formset, 'campaign': campaign,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})




@login_required
def public_campaign(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    # Filter public campaigns for the current user's profile
    public_campaigns = Campaign.objects.filter(visibility='public', user=user_profile).order_by('-timestamp')
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    return render(request, 'main/public_campaign.html', {'ads':ads,'public_campaigns': public_campaigns,  'user_profile': user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})





@login_required
def private_campaign(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]
    private_campaigns = Campaign.objects.filter(visibility='private', user=user_profile).order_by('-timestamp')
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)
    

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    return render(request, 'main/private_campaign.html', {
        'ads':ads,
        'private_campaigns': private_campaigns,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
      
    })





@login_required
def update_visibilit(request, campaign_id):
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)
    

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    campaign = get_object_or_404(Campaign, pk=campaign_id, user=request.user.profile)
    if request.method == 'POST':
        form = UpdateVisibilityForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('private_campaign')  # Redirect to the appropriate view
    else:
        form = UpdateVisibilityForm(instance=campaign)
 
    return render(request, 'main/update_visibilit.html', {
        'ads':ads,
        'form': form,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
      
    })







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






@login_required
def face(request):
    form = SubscriptionForm()
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Retrieve the latest campaign
    campaign = Campaign.objects.last()

    # Get the user's profile if the user is authenticated
    user_profile = None
    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)

    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Include user_profile and campaign in the render function
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    return render(request, 'main/face.html', {'ads':ads,'campaign': campaign, 'user_profile': user_profile,' unread_notifications': unread_notifications,'unread_notifications':new_campaigns_from_follows,'form':form,'ads':ads})


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


@login_required
def home(request):
    campaign = Campaign.objects.last()
    form = SubscriptionForm()
    user_profile = get_object_or_404(Profile, user=request.user)
    following_users = [follow.followed for follow in request.user.following.all()]

    # Filter public campaigns from users that the current user follows
    followed_public_campaigns = Campaign.objects.filter(user__user__in=following_users, visibility='public').distinct().order_by('-timestamp')

    # Filter public campaigns from the current user
    user_public_campaigns = Campaign.objects.filter(user=user_profile, visibility='public').distinct().order_by('-timestamp')

    # Combine both querysets
    public_campaigns = followed_public_campaigns | user_public_campaigns

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats, sender__id=request.user.id).exclude(sender=request.user).count()

    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()
    return render(request, 'main/home.html', {
        'ads': ads,
        'public_campaigns': public_campaigns,
        'campaign': campaign,
        'user_profile': user_profile,
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'form': form,
    })




def campaign_comments(request, campaign_id):
    # Retrieve campaign object
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile (assuming the user is authenticated)
    user_profile = get_object_or_404(Profile, user=request.user)
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        return HttpResponseForbidden("Campaign does not exist.")

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user.profile  # Assuming user is authenticated and has a profile
            comment.campaign_id = campaign_id
            comment.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = CommentForm()

    comments = Comment.objects.filter(campaign_id=campaign_id).order_by('-timestamp')  # Newest first
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)

    # Fetch unread messages for the user
    user_chats = Chat.objects.filter(participants=request.user)
    unread_messages_count = Message.objects.filter(chat__in=user_chats, sender__id=request.user.id).exclude(sender=request.user).count()

    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/campaign_comments.html', {'ads':ads,'campaign': campaign, 'comments': comments, 'form': form,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})



def campaign_support(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following

    support_campaign = SupportCampaign.objects.filter(campaign_id=campaign_id).first()

        # Get the user's profile if the user is authenticated
    user_profile = None
    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/campaign_support.html', {'ads':ads,'support_campaign': support_campaign,'user_profile':user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})


def recreate_campaign(request, campaign_id):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    categories = Campaign.CATEGORY_CHOICES  # Get the category choices from the Campaign model

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if form.is_valid():
            # Assuming you have a way to retrieve the existing campaign based on campaign_id
            existing_campaign = Campaign.objects.get(pk=campaign_id)

            # Update the existing campaign with the new data from the form
            existing_campaign.title = form.cleaned_data['title']
            existing_campaign.content = form.cleaned_data['content']
            existing_campaign.file = form.cleaned_data['file']
            existing_campaign.visibility = form.cleaned_data['visibility']

            existing_campaign.save()

            # Redirect the user to a success page or any other page
            return redirect('success_page')  # Replace 'success_page' with the appropriate URL name

    else:
        # Render the form with pre-filled data if it's a GET request
        # Assuming you have a way to retrieve the existing campaign based on campaign_id
        existing_campaign = Campaign.objects.get(pk=campaign_id)
        form = CampaignForm(instance=existing_campaign)  # Pass the existing campaign instance to pre-fill the form
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    return render(request, 'main/campaign_form.html', {'ads':ads,'form': form, 'categories': categories,'user_profile': user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})
def success_page(request):
    return render(request, 'main/success.html')

@login_required
def create_campaign(request):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Get the user's profile
    user_profile = get_object_or_404(Profile, user=request.user)
    categories = Campaign.CATEGORY_CHOICES  # Get the category choices from the Campaign model

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.user = request.user.profile  # Assuming profile is a one-to-one field on the User model
            campaign.save()
            return redirect('home')  # Redirect to a success page
    else:
        form = CampaignForm()
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save() 
    ads = NativeAd.objects.all()  
    return render(request, 'main/campaign_form.html', {'ads':ads,'form': form, 'categories': categories, 'user_profile': user_profile,'unread_notifications':unread_notifications,'new_campaigns_from_follows':new_campaigns_from_follows})


def follower_list(request, username):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    user = User.objects.get(username=username)
    followers = Follow.objects.filter(followed=user)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    context = {
        'ads':ads,
        'user': user,
        'followers': followers,
        'user_profile':user_profile,
        'unread_notifications':unread_notifications,
        'new_campaigns_from_follows':new_campaigns_from_follows
    }

    return render(request, 'main/follower_list.html', context)

def following_list(request, username):
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    user_profile = get_object_or_404(Profile, user=request.user)
    user = User.objects.get(username=username)
    following = Follow.objects.filter(follower=user)
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    # Check if there are new campaigns from follows
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    context = {
        'ads':ads,
        'user': user,
        'following': following,
        'user_profile':user_profile,
        'unread_notifications':unread_notifications,
        'new_campaigns_from_follows':new_campaigns_from_follows
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
    following_users = [follow.followed for follow in request.user.following.all()]  # Get users the current user is following
    # Fetch unread notifications for the user
    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    user_profile = get_object_or_404(Profile, user=request.user)
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)
    # Update last_campaign_check for the user's profile
    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)
    ads = NativeAd.objects.all()  
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile_view', username=username)
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    context = {
        'ads':ads,
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'username': username,
        'user_profile':user_profile,  # Pass the username to the context
        'unread_notifications':unread_notifications,
        'new_campaigns_from_follows':new_campaigns_from_follows
    }
    return render(request, 'main/edit_profile.html', context)


@login_required
def profile_view(request, username):
    following_users = [follow.followed for follow in request.user.following.all()]
    user_profile = get_object_or_404(Profile, user__username=username)

    followers_count = Follow.objects.filter(followed=user_profile.user).count()
    following_count = Follow.objects.filter(follower=user_profile.user).count()
    public_campaigns_count = user_profile.user_campaigns.filter(visibility='public').count()

    following_profile = False
    if request.user != user_profile.user:
        following_profile = Follow.objects.filter(follower=request.user, followed=user_profile.user).exists()

    unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
    new_campaigns_from_follows = Campaign.objects.filter(user__user__in=following_users, visibility='public', timestamp__gt=user_profile.last_campaign_check)

    user_profile.last_campaign_check = timezone.now()
    user_profile.save()
    ads = NativeAd.objects.all()  
    # Check if the user has more than 2 followers and update the is_verified field
    has_blue_tick = followers_count >= 2
    if user_profile.is_verified != has_blue_tick:
        user_profile.is_verified = has_blue_tick
        user_profile.save(update_fields=['is_verified'])

    context = {
        'ads':ads,
        'user_profile': user_profile,
        'following_profile': following_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'public_campaigns_count': public_campaigns_count,
        'unread_notifications': unread_notifications,
        'new_campaigns_from_follows': new_campaigns_from_follows,
        'has_blue_tick': has_blue_tick,  # This is just for display purposes
    }

    if 'search_query' in request.GET:
        form = ProfileSearchForm(request.GET)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            results = Profile.objects.filter(user__username__icontains=search_query)
            return render(request, 'main/search_profile_results.html', {'search_results': results, 'query': search_query})

    return render(request, 'main/user_profile.html', context)





def search_profile_results(request):
    if 'search_query' in request.GET:
        form = ProfileSearchForm(request.GET)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            results = Profile.objects.filter(user__username__icontains=search_query)
            return render(request, 'main/search_profile_results.html', {'search_results': results, 'query': search_query})
    return render(request, 'main/search_profile_results.html', {'search_results': [], 'query': ''})