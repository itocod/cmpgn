from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Case, When, Value, BooleanField
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest, JsonResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic.edit import DeleteView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

import paypalrestsdk
import os
import json
import base64
import time
import logging
import mimetypes
from decimal import Decimal
from dotenv import load_dotenv

from main.models import (
    Profile, Campaign, Comment, Follow, Activity, SupportCampaign, Brainstorming,
    User, Love, CampaignView, Chat, Notification, Message, CampaignFund,
    AffiliateLink, AffiliateLibrary, AffiliateNewsSource, NativeAd,
    Report, NotInterested, QuranVerse, Surah, Adhkar, Hadith,
    PlatformFund, Donation, CampaignProduct, ActivityComment, ActivityLove
)

from main.forms import (
    UserForm, ProfileForm, CampaignForm, CommentForm, ActivityForm, ActivityFormSet,
    SupportForm, ChatForm, MessageForm, CampaignSearchForm, ProfileSearchForm,
    BrainstormingForm, CampaignFundForm, CampaignProductForm, ReportForm, NotInterestedForm,
    SubscriptionForm, DonationForm, UpdateVisibilityForm, ActivityCommentForm,
    UserVerificationForm
)

from main.utils import calculate_similarity


from main.models import Campaign


def index(request):
    user_profile = None
    unread_notifications = []
    unread_messages_count = 0
    show_login_button = not request.user.is_authenticated  # Show the login button for anonymous users

    # Get selected category filter from request
    category_filter = request.GET.get('category', '')

    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)
        user_profile.last_campaign_check = timezone.now()
        user_profile.save()
        unread_notifications = Notification.objects.filter(user=request.user, viewed=False)
        user_chats = Chat.objects.filter(participants=request.user)
        unread_messages_count = Message.objects.filter(chat__in=user_chats).exclude(sender=request.user).count()

    # Fetch public campaigns, filter by category if selected
    campaigns = Campaign.objects.filter(visibility='public')

    if category_filter:
        campaigns = campaigns.filter(category=category_filter)

    campaigns = campaigns.select_related('user') \
        .annotate(love_count_annotated=Count('loves')) \
        .filter(love_count_annotated__gte=1) \
        .order_by('-love_count_annotated')

    # Fetch available categories
    categories = Campaign.objects.values_list('category', flat=True).distinct()

    form = SubscriptionForm()
    ads = NativeAd.objects.all()

    context = {
        'campaigns': campaigns,
        'user_profile': user_profile,  # None for anonymous users
        'unread_notifications': unread_notifications,
        'unread_messages_count': unread_messages_count,
        'form': form,
        'ads': ads,
        'show_login_button': show_login_button,  # Add the flag to context
        'categories': categories,  # Pass categories to template
        'selected_category': category_filter,  # Retain selected category
    }

    return render(request, 'accounts/index.html', context)







def home(request):
    # Your view logic here...
    return render(request, 'accounts/home.html', {})




def face(request):
    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)
    else:
        user_profile = None  # Handle the case where the user is not authenticated or no profile is found

    context = {'user_profile': user_profile}
    return render(request, 'accounts/face.html', context)