import datetime
import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
from django.utils import timezone
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from PIL import Image
from tinymce.models import HTMLField  
from django.urls import reverse
from io import BytesIO
from django.core.files.base import ContentFile



User = get_user_model()

class Profile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    EDUCATION_CHOICES = (
        ('None', 'None'),
        ('Some High School', 'Some High School'),
        ('High School Graduate', 'High School Graduate'),
        ('Some College', 'Some College'),
        ('Associate\'s Degree', 'Associate\'s Degree'),
        ('Bachelor\'s Degree', 'Bachelor\'s Degree'),
        ('Master\'s Degree', 'Master\'s Degree'),
        ('PhD', 'PhD'),
        ('Other', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics', default='profile_pics/pp.png')
    bio = models.TextField(default='No bio available')
    contact = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    highest_level_of_education = models.CharField(max_length=100, choices=EDUCATION_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    campaigns = models.ManyToManyField('Campaign', related_name='user_profiles', blank=True)
    following = models.ManyToManyField(User, related_name='following_profiles')
    followers = models.ManyToManyField(User, related_name='follower_profiles')
    last_campaign_check = models.DateTimeField(default=timezone.now)
    last_chat_check = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def followers_count(self):
        return self.followers.all().count()

    def following_count(self):
        return self.following.all().count()

    def has_exactly_two_followers(self):
        return self.followers_count() == 2

        
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            return age
            return None


    def update_verification_status(self):
        self.is_verified = self.followers_count() >= 2
        self.save(update_fields=['is_verified'])

        
    def followers_count(self):
        return self.user.followers.count()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Handle image processing
        if self.image:
            img = Image.open(self.image)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)

                # Save the processed image
                buffer = BytesIO()
                img.save(buffer, format=img.format)
                buffer.seek(0)
                self.image.save(self.image.name, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} Profile'






@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.follower} follows {self.followed}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Update the followed user's profile verification status
            self.followed.profile.update_verification_status()
            
            # Create the notification message
            follower_username = self.follower.username
            followed_username = self.followed.username
            message = f"{follower_username} started following you. <a href='{reverse('profile_view', kwargs={'username': follower_username})}'>View Profile</a>"
            # Create the notification
            Notification.objects.create(user=self.followed, message=message)



def default_content():
    return 'Default content'

         

class Brainstorming(models.Model):
    idea = HTMLField() 
    supporter = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Create the notification message
            supporter_username = self.supporter.username
            campaign_title = self.campaign.title
            message = f"{supporter_username} has added a new brainstorming idea to your campaign '{campaign_title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
            
            # Create the notification
            Notification.objects.create(user=self.campaign.user.user, message=message, campaign=self.campaign)

class Campaign(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='user_campaigns')
    title = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    file = models.FileField(upload_to='campaign_files/', null=True, blank=True)

    CATEGORY_CHOICES = (
        ('Awareness', 'Awareness'),
        ('Fundraising', 'Fundraising'),
        ('Volunteering', 'Volunteering'),
        ('Education', 'Education'),
        ('Healthcare', 'Healthcare'),
        ('Environment', 'Environment'),
        ('Animal Welfare', 'Animal Welfare'),
        ('Arts and Culture', 'Arts and Culture'),
        ('Sports', 'Sports'),
        ('Technology', 'Technology'),
        ('Community Development', 'Community Development'),
        ('Human Rights', 'Human Rights'),
        ('Emergency Relief', 'Emergency Relief'),
        ('Political Campaigns', 'Political Campaigns'),
        ('Business and Entrepreneurship', 'Business and Entrepreneurship'),
        ('Religious', 'Religious'),
        ('Other', 'Other'),
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Awareness')
    
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    
    allowed_viewers = models.ManyToManyField(Profile, related_name='allowed_campaigns', blank=True)
    
    def __str__(self):
        return self.title

    @property
    def love_count(self):
        return self.loves.count()

    def get_objective_and_activities(self):
        objectives_activities = {
            'Awareness': {
                'Objectives': [
                    'Educate the public about a specific issue or cause.',
                    'Raise consciousness and encourage action related to the cause.',
                ],
                'Activities': [
                    'Organize awareness events (e.g., workshops, seminars, webinars).',
                    'Distribute educational materials (e.g., flyers, infographics).etc',
                    
                ]
            },
            'Fundraising': {
                'Objectives': [
                    'Raise funds to support a specific cause or project.',
                    'Increase awareness about the fundraising campaign.',
                ],
                'Activities': [
    
                    'Organize fundraising events (e.g., charity galas, auctions).',
                    'Seek corporate sponsorships and partnerships. etc',
                ]
            },
            'Volunteering': {
                'Objectives': [
                    'Recruit volunteers to contribute time and skills to a cause.',
                    'Engage the community in meaningful volunteer activities.',
                ],
                'Activities': [
                    'Host volunteer recruitment drives.',
                    'Organize volunteer training sessions.',
                    'Coordinate volunteer activities (e.g., community clean-ups, mentoring programs).etc',
                ]
            },
            'Education': {
                'Objectives': [
                    'Promote and facilitate learning opportunities within a community.',
                    'Improve access to education resources and support.',
                ],
                'Activities': [
                    'Offer tutoring or mentoring programs for students.',
                    'Organize workshops or conferences on educational topics.etc',
                ]
            },
            'Healthcare': {
                'Objectives': [
                    'Improve healthcare access or services for a specific population.',
                    'Raise awareness about healthcare issues or conditions.',
                ],
                'Activities': [
                    'Organize health screenings or vaccination drives.',
                    'Fundraise for medical treatments or equipment.',
                    'Advocate for healthcare policy changes.etc',
                ]
            },
            'Environment': {
                'Objectives': [
                    'Promote environmental conservation and sustainability practices.',
                    'Protect endangered species or ecosystems.',
                ],
                'Activities': [
                    'Organize clean-up events for beaches, parks, or urban areas.',
                    'Plant trees or establish community gardens.',
                    'Advocate for environmental legislation or initiatives.etc',
                ]
            },
            'Animal Welfare': {
                'Objectives': [
                    'Promote the welfare and rights of animals.',
                    'Rescue and provide care for animals in need.',
                ],
                'Activities': [
                    'Fundraise for animal shelters or rescue organizations.',
                    'Advocate for animal protection laws or policies.',
                    'Organize adoption events or pet care workshops.etc',
                ]
            },
            'Arts and Culture': {
                'Objectives': [
                    'Promote artistic expression and cultural diversity.',
                    'Preserve and celebrate cultural heritage.',
                ],
                'Activities': [
                    'Organize art exhibitions, performances, or cultural festivals.',
                    'Provide arts education programs for youth or underserved communities.',
                    'Support local artists and cultural initiatives.etc',
                ]
            },
            'Sports': {
                'Objectives': [
                    'Promote physical activity, sportsmanship, and teamwork.',
                    'Provide opportunities for community engagement through sports.',
                ],
                'Activities': [
                    'Organize sports tournaments or recreational leagues.',
                    'Offer sports clinics or training programs.',
                    'Support athletes or teams in need of financial assistance.etc',
                ]
            },
            'Technology': {
                'Objectives': [
                    'Promote innovation and technological advancements.',
                    'Increase access to technology and digital literacy.',
                ],
                'Activities': [
                    'Launch tech startup incubator programs.',
                    'Organize hackathons or coding workshops.',
                    'Provide access to computers or internet in underserved areas. etc',
                ]
            },
            'Community Development': {
                'Objectives': [
                    'Improve infrastructure and amenities within a community.',
                    'Foster social cohesion and civic engagement.',
                ],
                'Activities': [
                    'Organize community clean-up or beautification projects.',
                    'Advocate for improvements in housing or public spaces.',
                    'Establish community centers or hubs for social activities.etc',
                ]
            },
            'Human Rights': {
                'Objectives': [
                    'Promote and protect human rights and freedoms.',
                    'Raise awareness about social justice issues.',
                ],
                'Activities': [
                    'Organize rallies, marches, or protests.',
                    'Support legal aid or advocacy campaigns.',
                    'Educate the public about human rights violations.etc',
                ]
            },
            'Emergency Relief': {
                'Objectives': [
                    'Provide immediate assistance to individuals or communities in crisis.',
                    'Prepare for and respond to natural disasters or emergencies.',
                ],
                'Activities': [
                    'Fundraise for emergency relief supplies or shelters.',
                    'Coordinate relief efforts with local authorities or organizations.',
                    'Offer psychological support or trauma counseling.etc',
                ]
            },
            'Political Campaigns': {
                'Objectives': [
                    'Support candidates or advocate for specific political issues.',
                    'Mobilize voters and increase political participation.',
                ],
                'Activities': [
                    'Organize campaign rallies or town hall meetings. etc',
        
                    
                ]
            },
            'Business and Entrepreneurship': {
                'Objectives': [
                    'Support startups, small businesses, or entrepreneurial ventures.',
                    'Promote economic growth and job creation.',
                ],
                'Activities': [
                    'Provide mentoring or coaching for aspiring entrepreneurs.',

                    'Organize networking events or pitch competitions. etc',
                ]
            },
            'Religious': {
                'Objectives': [
                    'Promote spiritual growth and religious education.',
                    'Support religious communities and charitable outreach.',
                ],
                'Activities': [
                    'Organize religious services, retreats, or study groups.',
                    'Fundraise for religious charities or missions.',
                    'Support community service projects aligned with religious values. etc',
                ]
            },
            'Other': {
                'Objectives': [
                    'Support miscellaneous causes or initiatives not covered by other categories.',
                ],
                'Activities': [
                    'Tailor  activities based on the specific nature of the campaign.',
                ]
            },
        }
        return objectives_activities.get(self.category, {})


class Report(models.Model):
    REASON_CHOICES = (
        ('Spam', 'Spam'),
        ('Inappropriate Content', 'Inappropriate Content'),
        ('Copyright Violation', 'Copyright Violation'),
        ('Fraud', 'Fraud'),
        ('Other', 'Other'),
    )
    
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Report by {self.reported_by} on {self.campaign}'




class NotInterested(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='not_interested_campaigns')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='not_interested_by')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.user.username} not interested in {self.campaign.title}'







class SupportCampaign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE)
    
    CATEGORY_CHOICES = (
        (' Donate_monetary,', ' Donate_monetary,'),
        ('Brainstorming', 'Brainstorming'),
        ('CampaignProduct','CampaignProduct')
     
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Monetary Donation')
    
    # Visibility fields for support actions
    donate_monetary_visible = models.BooleanField(default=True)
    brainstorm_idea_visible = models.BooleanField(default=True)
      # Visibility for campaign products
    campaign_product_visible = models.BooleanField(default=True)
   





class CampaignProduct(models.Model):
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=200)
    image = models.ImageField(upload_to='campaign_product_images/', blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, default='default_category')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=timezone.now)  # Use timezone.now() as default

    def __str__(self):
        return self.name




class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    donation_link = models.URLField(max_length=200)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Donation to {self.donation_link} by {self.user}"





class CampaignView(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)  # Allow null values for the user field
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    time_spent = models.DurationField(default=timezone.timedelta(minutes=0))

    class Meta:
        unique_together = ('user', 'campaign')






class Love(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='loves')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new love
            # Create the notification message
            campaign_title = self.campaign.title
            message = f"{self.user.username} loved your campaign '{campaign_title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
            # Create the notification
            Notification.objects.create(user=self.campaign.user.user, message=message)
        super().save(*args, **kwargs)








class Comment(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField(default='say something..')

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new comment
            # Create the notification message
            commenter_username = self.user.user.username
            message = f"{commenter_username} commented on your campaign '{self.campaign.title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
            # Create the notification
            Notification.objects.create(user=self.campaign.user.user, message=message)
        super().save(*args, **kwargs)






class Activity(models.Model):
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE)
    content = models.TextField(default='content')
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='activity_file', blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new activity
            # Create the notification message for the campaign owner
            message_owner = f"An activity was added to your campaign '{self.campaign.title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
            # Create the notification for the campaign owner
            Notification.objects.create(user=self.campaign.user.user, message=message_owner)
            followers = self.campaign.user.followers.all()
            for follower in followers:
                message_follower = f"An activity was added to a campaign you're following: '{self.campaign.title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
                Notification.objects.create(user=follower, message=message_follower)


        super().save(*args, **kwargs)







class ActivityLove(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='loves')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new love
            # Create the notification message
            message = f"{self.user.username} loved an activity in your campaign '{self.activity.campaign.title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.activity.campaign.pk})}'>View Campaign</a>"
            # Create the notification
            Notification.objects.create(user=self.activity.campaign.user.user, message=message)
        super().save(*args, **kwargs)


class ActivityComment(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content =  models.TextField(default='say something..')
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new comment
            # Create the notification message
            message = f"{self.user.username} commented on an activity in your campaign '{self.activity.campaign.title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.activity.campaign.pk})}'>View Campaign</a>"
            # Create the notification
            Notification.objects.create(user=self.activity.campaign.user.user, message=message)
        super().save(*args, **kwargs)





class Chat(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_chats', default=None)
    participants = models.ManyToManyField(User, related_name='chats')
    title = models.CharField(max_length=100, default='')  
    created_at = models.DateTimeField(auto_now_add=True)

    def has_unread_messages(self, last_chat_check):
        return self.messages.filter(timestamp__gt=last_chat_check).exists()

    def __str__(self):
        return f"{self.title} (ID: {self.id})"

@receiver(m2m_changed, sender=Chat.participants.through)
def notify_user_added(sender, instance, action, model, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            message = f"You have been added to the chat '{instance.title}'. <a href='{reverse('chat_detail', kwargs={'chat_id': instance.pk})}'>View Chat</a>"
            Notification.objects.create(user=user, message=message)




class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(default='say something..')
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new message
            # Create the notification message
            message = f"You have a new message from {self.sender.username} in the chat '{self.chat.title}'. <a href='{reverse('chat_detail', kwargs={'chat_id': self.chat.pk})}'>View Chat</a>"
            # Notify all participants except the sender
            for participant in self.chat.participants.exclude(id=self.sender.id):
                Notification.objects.create(user=participant, message=message)
        super().save(*args, **kwargs)








class AffiliateLink(models.Model):
    title = models.CharField(max_length=200)
    link = models.URLField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='affiliate_images/', null=True, blank=True)

    def __str__(self):
        return self.title





class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)
    campaign_notification = models.BooleanField(default=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True)
    redirect_link = models.URLField(blank=True, null=True)  # Add a field for the redirect link

    def __str__(self):
        return self.message

class Surah(models.Model):
    name = models.CharField(max_length=255)
    surah_number = models.IntegerField(unique=True)
    chapter = models.IntegerField(default=1)
    english_name = models.CharField(max_length=255, default='unknown')
    place_of_revelation = models.CharField(max_length=255, default='unknown')

    def __str__(self):
        return self.name

class QuranVerse(models.Model):
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE)
    verse_number = models.IntegerField()
    verse_text = models.TextField()
    translation = models.TextField()
    description = models.TextField(blank=True, null=True)  # New description field

    class Meta:
        unique_together = ('surah', 'verse_number')

    def __str__(self):
        return f"{self.surah.name} {self.verse_number}"


class Adhkar(models.Model):
    TYPE_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('after_prayer', 'After Prayer'),
        ('anywhere', 'Anywhere'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text = models.TextField()
    translation = models.TextField()
    reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.get_type_display()} Adhkar"


class Hadith(models.Model):
    narrator = models.CharField(max_length=255)
    text = models.TextField()
    reference = models.CharField(max_length=255)
    authenticity = models.CharField(max_length=100)

    def __str__(self):
        return f"Hadith {self.id}: {self.reference}"



class PlatformFund(models.Model):
    donation_link = models.URLField(max_length=200)

    def __str__(self):
        return self.donation_link


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email



class AffiliateLibrary(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField()
    affiliate_link = models.URLField()
    description = models.TextField(blank=True)
    # Add more fields as needed, such as commission rate, affiliate program details, etc.

class AffiliateNewsSource(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField()
    affiliate_link = models.URLField()
    description = models.TextField(blank=True)
    # Add more fields as needed, such as commission rate, affiliate program details, etc



class NativeAd(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='native_ads/')
    link = models.URLField()
    sponsored_by = models.CharField(max_length=100)

    def __str__(self):
        return self.title