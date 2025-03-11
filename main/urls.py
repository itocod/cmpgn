from django.urls import path, include
from . import views
from .views import CustomLoginView
from .views import CampaignDeleteView

urlpatterns = [
path('campaigns/', views.campaign_list, name='campaign_list'),

   path('campaign/<int:campaign_id>/engagement/', views.campaign_engagement_data, name='campaign_engagement'),
    path('landing/', views.explore_campaigns, name='explore_campaigns'),
    path('verify/', views.verify_profile, name='verify_profile'),
    path('campaign/<int:campaign_id>/join_leave/', views.join_leave_campaign, name='join_leave_campaign'),
    path('campaign/<int:campaign_id>/joiners/', views.campaign_joiners, name='campaign_joiners'),
    path('donate/<int:campaign_id>/', views.donate, name='donate'),
    path('payment-success/<int:campaign_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('campaign/delete/<int:pk>/', CampaignDeleteView.as_view(), name='campaign-delete'),
    path('libraries/', views.library_affiliates, name='library_affiliates'),
    path('news/', views.news_affiliates, name='news_affiliates'),
    path('poster-canva/', views.poster_canva, name='poster_canva'),
       path('login/', CustomLoginView.as_view(), name='login'),
  
    path('rallynex-logo/', views.rallynex_logo, name='rallynex_logo'),
   path('campaign/<int:campaign_id>/update_visibilit/', views.update_visibilit, name='update_visibilit'),

    path('subscribe/', views.subscribe, name='subscribe'),
    path('jobs/', views.jobs, name='jobs'),
    path('events/', views.events, name='events'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('project_support/', views.project_support, name='project_support'),

    path('campaign/<int:campaign_id>/top-participants/', views.top_participants_view, name='top_participants'),
     path('quran/', views.quran_view, name='quran_view'),
    path('adhkar/', views.adhkar_list, name='adhkar_list'),
    path('adhkar/<int:adhkar_id>/', views.adhkar_detail, name='adhkar_detail'),
       path('hadith/', views.hadith_list, name='hadith_list'),
    path('hadith/<int:hadith_id>/', views.hadith_detail, name='hadith_detail'),
    # Other URL patterns...
      # Other URL patterns for your project
      path('campaigns/mark_not_interested/<int:campaign_id>/', views.mark_not_interested, name='mark_not_interested'),
    path('campaign/<int:campaign_id>/report/',views.report_campaign, name='report_campaign'),
    path('upload_image/',views.upload_image, name='upload_image'),
    path('campaign/<int:campaign_id>/product/', views.product_manage, name='product_manage'),
    path('campaign/<int:campaign_id>/product/<int:product_id>/', views.product_manage, name='product_edit'),
    # Other URL patterns.
     path('changemakers/', views.changemakers_view, name='changemakers_view'),
    path('love_activity/<int:activity_id>/', views.love_activity, name='love_activity'),
   path('activity/<int:activity_id>/', views.activity_detail, name='activity_detail'),

    path('delete/<int:campaign_id>/', views.delete_campaign, name='delete_campaign'),
    path('activity/<int:activity_id>/add_comment/', views.add_activity_comment, name='add_activity_comment'),
    path('suggest/', views.suggest, name='suggest'),
         path('campaign/<int:campaign_id>/donate/', views.donate, name='donate'),
    path('affiliate-links/', views.affiliate_links, name='affiliate_links'),

     path('platformfund/', views.platformfund_view, name='platformfund'),
       
    path('campaign/<int:campaign_id>/', views.view_campaign, name='view_campaign'),  # Corrected URL pattern
    path('update_visibility/<int:campaign_id>/', views.update_visibility, name='update_visibility'),
    path('update_hidden_links/', views.update_hidden_links, name='update_hidden_links'),
 path('upload/', views.upload_file, name='upload_file'),
    path('brainstorm_idea/<int:campaign_id>/', views.brainstorm_idea, name='brainstorm_idea'),
    path('campaign/<int:campaign_id>/donate', views.donate_monetary, name='donate_monetary'),
    path('search_profile_results/', views.search_profile_results, name='search_profile_results'),
    path('search/', views.search_campaign, name='search_campaign'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('create-chat/', views.create_chat, name='create_chat'),
    path('chat-detail/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('user/chats/', views.user_chats, name='user_chats'),
    path('chat/<int:chat_id>/add_participants/', views.add_participants, name='add_participants'),
    path('chat/<int:chat_id>/remove_participants/', views.remove_participants, name='remove_participants'),
    path('chat/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('campaign/<int:campaign_id>/toggle-love/', views.toggle_love, name='toggle_love'),
    path('campaign/<int:campaign_id>/support/', views.support, name='support'),
    path('campaign/<int:campaign_id>/support-campaign/', views.campaign_support, name='campaign_support'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('home', views.home, name='home'),
    path('manage_campaigns/', views.manage_campaigns, name='manage_campaigns'),
    path('face', views.face, name='face'),
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('edit-profile/<str:username>/', views.profile_edit, name='edit_profile'),
    path('user-profile/<str:username>/', views.profile_view, name='profile_view'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('followers/<str:username>/', views.follower_list, name='follower_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
    path('private-campaign/', views.private_campaign, name='private_campaign'),
    path('recreate-campaign/<int:campaign_id>/', views.recreate_campaign, name='recreate_campaign'),
     path('success/', views.success_page, name='success_page'),
    path('campaign/<int:campaign_id>/activity/create/', views.create_activity, name='create_activity'),
    path('campaign/<int:campaign_id>/activity_list/', views.activity_list, name='activity_list'),
    path('campaign/<int:campaign_id>/comments/', views.campaign_comments, name='campaign_comments'),


# marketing 

    path('blog/', views.blog_list, name='blog_list'),  # List of all blogs
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),  # Single blog post


]







