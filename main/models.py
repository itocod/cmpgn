import datetime
import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from tinymce.models import HTMLField
from django.db.models.signals import m2m_changed
from django.urls import reverse
from PIL import Image, ExifTags
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
    image = models.ImageField(upload_to='profile_pics/', default='profile_pics/pp.png', max_length=255)
    bio = models.TextField(default='No bio available')
    contact = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    highest_level_of_education = models.CharField(max_length=100, choices=EDUCATION_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    campaigns = models.ManyToManyField('Campaign', related_name='user_profiles', blank=True)
    following = models.ManyToManyField(User, related_name='following_profiles', blank=True)
    followers = models.ManyToManyField(User, related_name='follower_profiles', blank=True)
    last_campaign_check = models.DateTimeField(default=timezone.now)
    last_chat_check = models.DateTimeField(default=timezone.now)
    profile_verified = models.BooleanField(default=False)  # Renamed from `is_verified
    # Other fields...

 

    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            return age
        return None

    def update_verification_status(self):
        """Update verification status."""
        self.profile_verified = True  # Mark the profile as verified
        self.save(update_fields=['profile_verified'])


    def __str__(self):
        return f'{self.user.username} Profile'

    @property
    def total_loves(self):
        # Sum the loves for all campaigns owned by the user
        return Love.objects.filter(campaign__user=self).count()

    def is_changemaker(self):
    # Correct the query to reflect the relationship with the Campaign model
        activity_count = Activity.objects.filter(campaign__user=self).count()  # `campaign__user` references the Profile
        activity_love_count = ActivityLove.objects.filter(activity__campaign__user=self).count()

        return activity_count >= 1 and activity_love_count >= 1




@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class UserVerification(models.Model):
    VERIFICATION_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    document_type = models.CharField(max_length=100, choices=(
        ('National ID', 'National ID'),
        ('Business Certificate', 'Business Certificate'),
    ))
    document = models.FileField(upload_to='verification_docs/')
    submission_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='Pending')
    rejection_reason = models.TextField(blank=True, null=True)
    verified_on = models.DateTimeField(blank=True, null=True)

    def approve(self):
        """Approve the verification and set the verified date."""
        self.status = 'Approved'
        self.verified_on = timezone.now()
        self.save()
        # Create a notification for the user
        Notification.objects.create(user=self.user, message=f"Your verification for {self.document_type} has been approved.")

    def reject(self, reason):
        """Reject the verification and set the rejection reason."""
        self.status = 'Rejected'
        self.rejection_reason = reason
        self.save()
        self.notify_user()  # Notify the user upon rejection

    def notify_user(self):
        """Notify the user about the rejection."""
        message = f"Your verification for {self.document_type} has been rejected. Reason: {self.rejection_reason}."
        Notification.objects.create(user=self.user, message=message)

    def __str__(self):
        return f"Verification of {self.user.username} - {self.document_type}"

    class Meta:
        verbose_name = 'User Verification'
        verbose_name_plural = 'User Verifications'
        ordering = ['-submission_date']


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Profile)
def update_user_verification_status(sender, instance, created, **kwargs):
    if instance.profile_verified:  # Use the new field name
        verification = UserVerification.objects.filter(user=instance.user).first()
        if verification and verification.status != 'Approved':
            verification.approve()
            verification.verified_on = timezone.now()
            verification.save()




class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.follower} follows {self.followed}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # No need to call update_verification_status() anymore
            # Notify the followed user
            follower_username = self.follower.username
            followed_username = self.followed.username
            message = f"{follower_username} started following you. <a href='{reverse('profile_view', kwargs={'username': follower_username})}'>View Profile</a>"
            Notification.objects.create(user=self.followed, message=message)





def default_content():
    return 'Default content'

         


class Brainstorming(models.Model):
    idea = models.TextField() 
    attachment = models.FileField(upload_to='brainstorming_attachments/', blank=True, null=True)
    supporter = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            supporter_username = self.supporter.username
            campaign_title = self.campaign.title
            message = f"{supporter_username} has added a new brainstorming idea to your campaign '{campaign_title}'. <a href='{reverse('view_campaign', kwargs={'campaign_id': self.campaign.pk})}'>View Campaign</a>"
            Notification.objects.create(user=self.campaign.user.user, message=message, campaign=self.campaign)

from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError





class Campaign(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='user_campaigns')
    title = models.CharField(max_length=300)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    poster = models.ImageField(upload_to='campaign_files', null=True, blank=True)
    audio = models.FileField(upload_to='campaign_audio', null=True, blank=True)

    CATEGORY_CHOICES = (
        ('Environmental Conservation', 'Environmental Conservation'),
        ('Community Development', 'Community Development'),
        ('Health and Wellness', 'Health and Wellness'),
        ('Education and Literacy', 'Education and Literacy'),
        ('Equality and Inclusion', 'Equality and Inclusion'),
        ('Animal Welfare', 'Animal Welfare'),
        ('Humanitarian Aid', 'Humanitarian Aid'),
        ('Sustainable Development', 'Sustainable Development'),
        ('Peace and Conflict Resolution', 'Peace and Conflict Resolution'),
        ('Digital Rights', 'Digital Rights'),
        ('Economic Empowerment', 'Economic Empowerment'),
        ('Policy Advocacy', 'Policy Advocacy'),
        ('Artistic Advocacy', 'Artistic Advocacy'),
        ('Other', 'Other'),
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Environmental Conservation')
 
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')

    # Followers who can see the campaign when it's private
    visible_to_followers = models.ManyToManyField(Profile, blank=True, related_name='visible_campaigns')
    

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Check if the campaign is new or if visibility has changed
        is_new = self.pk is None
        if not is_new:
            old_instance = Campaign.objects.get(pk=self.pk)
            visibility_changed = old_instance.visibility != self.visibility
        else:
            visibility_changed = False

        # Save the campaign
        super().save(*args, **kwargs)

        # Notify followers if the campaign has become private or if it's a new campaign
        if self.visibility == 'private' or is_new:
            if is_new or visibility_changed:
                self.notify_visible_to_followers()

    def notify_visible_to_followers(self):
        for profile in self.visible_to_followers.all():
            user = profile.user  # Ensure this relationship is correctly set
            message = (
                f'You have been granted access to a private campaign: {self.title}. '
                f'<a href="{reverse("view_campaign", kwargs={"campaign_id": self.pk})}">View Campaign</a>'
            )
            Notification.objects.create(
                user=user,
                message=message,
                timestamp=timezone.now(),
                campaign_notification=True,
                campaign=self,
                redirect_link=f'/campaigns/{self.pk}/'
            )


    @property
    def love_count(self):
        return self.loves.count()
        

    @property
    def is_changemaker(self):
        """Check if the user qualifies as a changemaker."""
        activity_count = self.activity_set.count()
        activity_love_count = ActivityLove.objects.filter(activity__campaign=self).count()
        return activity_count >= 1 and activity_love_count >= 1

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Automatically award changemaker status if criteria are met
        if self.is_changemaker:
            self.award_changemaker_status()

    def award_changemaker_status(self):
        """Award changemaker status and assign the correct award type."""
        # Check if the user already has an award for this campaign
        if not ChangemakerAward.objects.filter(user=self.user, campaign=self).exists():
            # Determine the number of campaigns with changemaker status
            changemaker_campaigns = Campaign.objects.filter(user=self.user, activity__isnull=False).distinct()

            # Assign the award based on the number of changemaker campaigns
            campaign_count = changemaker_campaigns.count()
            if campaign_count >= 3:
                award_type = 'Gold'
            elif campaign_count >= 2:
                award_type = 'Silver'
            else:
                award_type = 'Bronze'

            # Create the award entry
            ChangemakerAward.objects.create(
                user=self.user,
                campaign=self,
                award=award_type,
                timestamp=timezone.now()
            )

    def get_objective_and_activities(self):
        objectives_activities = {
         'Environmental Conservation': {
    'Objectives': [
        'Promote environmental conservation and sustainability practices.',
        'Protect endangered species or ecosystems.',
    ],
    'Activities': [
        'Organize clean-up events for beaches, parks, or urban areas.',
        'Plant trees or establish community gardens.',
        'Advocate for environmental legislation or initiatives.',
        'Fundraise for conservation efforts or endangered species programs.',
        'Host workshops or events on sustainable living practices.',
        'Collaborate with wildlife experts or organizations to protect endangered species.',
        'Initiate habitat restoration projects for ecosystems in danger.',
        'Raise awareness about conservation issues through  campaigns.',
        'Organize petition campaigns to support environmental laws and policies.',
        'Partner with local environmental organizations to scale conservation efforts.',
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
        'Establish community centers or hubs for social activities.',
        'Create programs to support local businesses or entrepreneurs.',
        'Organize neighborhood safety initiatives or watch groups.',
        'Host cultural or social events to strengthen community bonds.',
        'Develop mentorship or educational programs for youth or underprivileged groups.',
        'Raise funds for infrastructure projects, such as parks or playgrounds.',
        'Promote volunteerism within the community to address local issues.',
        'Collaborate with local government to address specific community needs.',
    ]
},
'Health and Wellness': {
    'Objectives': [
        'Promote health and wellness initiatives.',
        'Raise awareness about healthcare issues or conditions.',
    ],
    'Activities': [
        'Organize health screenings or vaccination drives.',
        'Fundraise for medical treatments or equipment.',
        'Advocate for healthcare policy changes.',
        'Host workshops or seminars on healthy living and disease prevention.',
        'Collaborate with local health professionals to provide free medical consultations.',
        'Raise awareness about mental health through campaigns or workshops.',
        'Organize fitness challenges or community exercise programs.',
        'Establish support groups for individuals dealing with chronic illnesses or conditions.',
        'Promote nutritional education and healthy eating habits.',
        'Partner with healthcare providers to offer discounted or free services for underserved populations.',
    ]
},

'Education and Literacy': {
    'Objectives': [
        'Promote and facilitate learning opportunities within a community.',
        'Improve access to education resources and support.',
    ],
    'Activities': [
        'Offer tutoring or mentoring programs for students.',
        'Organize workshops or conferences on educational topics.',
        'Raise funds to provide educational materials or scholarships for underprivileged students.',
        'Establish community libraries or book donation drives.',
        'Collaborate with educators to create after-school programs or learning clubs.',
        'Host literacy campaigns aimed at reducing illiteracy rates in underserved areas.',
        'Promote digital literacy and access to technology through training programs.',
        'Create parent education initiatives to help families support their children’s learning.',
        'Develop vocational training programs to improve job readiness.',
        'Partner with local schools or educational institutions to expand learning resources.',
    ]
},

  'Equality and Inclusion': {
    'Objectives': [
        'Promote equality, diversity, and inclusion.',
        'Advocate for the rights of marginalized communities.',
    ],
    'Activities': [
        'Organize awareness campaigns and educational seminars.',
        'Support social justice initiatives and advocacy efforts.',
        'Host diversity training programs for organizations and community groups.',
        'Create safe spaces for marginalized communities to share their experiences.',
        'Collaborate with legal experts to provide pro bono services for marginalized individuals.',
        'Launch mentorship programs aimed at empowering underrepresented groups.',
        'Advocate for policy changes that address inequality and discrimination.',
        'Promote inclusive hiring practices through partnerships with businesses.',
        'Raise funds for organizations that support equality and inclusion initiatives.',
        'Host cultural exchange events to celebrate diversity and foster understanding.',
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
        'Organize adoption events or pet care workshops.',
        'Create and distribute educational materials on responsible pet ownership.',
        'Collaborate with veterinarians to offer free or low-cost medical services.',
        'Host spay and neuter clinics to control pet overpopulation.',
        'Develop outreach programs to educate the public about animal welfare issues.',
        'Establish a network of foster homes for animals awaiting adoption.',
        'Organize volunteer opportunities to support animal shelters and rescue groups.',
        'Promote and support wildlife conservation efforts to protect endangered species.',
    ]
},

'Humanitarian Aid': {
    'Objectives': [
        'Provide humanitarian assistance to communities in need.',
        'Respond to humanitarian crises and emergencies.',
    ],
    'Activities': [
        'Fundraise for humanitarian relief efforts.',
        'Coordinate aid distribution and relief operations.',
        'Provide medical care and essential supplies.',
        'Organize and support emergency response teams for disaster relief.',
        'Partner with local organizations to deliver targeted aid in affected areas.',
        'Conduct needs assessments to identify and address critical gaps in aid.',
        'Host community workshops to educate on disaster preparedness and response.',
        'Develop and maintain emergency preparedness plans for future crises.',
        'Raise awareness and advocate for support for humanitarian causes.',
        'Collaborate with international agencies to coordinate global relief efforts.',
    ]
},

'Sustainable Development': {
    'Objectives': [
        'Promote sustainable development practices.',
        'Support initiatives for long-term environmental and social sustainability.',
    ],
    'Activities': [
        'Implement renewable energy projects.',
        'Advocate for sustainable agriculture and resource management.',
        'Educate communities about sustainable living practices.',
        'Develop and support green building projects or energy-efficient infrastructure.',
        'Organize community workshops on waste reduction and recycling.',
        'Support initiatives for water conservation and management.',
        'Promote sustainable transportation options, such as biking and public transit.',
        'Partner with local businesses to adopt sustainable practices.',
        'Raise awareness about climate change and its impacts through campaigns or events.',
        'Facilitate collaborations between stakeholders to advance sustainability goals.',
    ]
},

'Peace and Conflict Resolution': {
    'Objectives': [
        'Promote peacebuilding and conflict resolution.',
        'Support reconciliation and peace initiatives.',
    ],
    'Activities': [
        'Organize peacebuilding workshops and dialogues.',
        'Support mediation and dialogue processes.',
        'Advocate for peace and disarmament policies.',
        'Facilitate community-led conflict resolution programs.',
        'Partner with local and international organizations to support peace initiatives.',
        'Host educational events on conflict resolution skills and techniques.',
        'Develop and implement reconciliation programs for post-conflict communities.',
        'Promote cross-cultural exchange programs to foster understanding and tolerance.',
        'Raise awareness about the impacts of conflict and the benefits of peace through campaigns.',
        'Support initiatives that address the root causes of conflict, such as poverty or inequality.',
    ]
},
'Digital Rights': {
    'Objectives': [
        'Advocate for digital rights and online privacy protection.',
        'Promote internet freedom and access to information.',
    ],
    'Activities': [
        'Campaign for digital rights legislation and policies.',
        'Raise awareness about online security and data privacy issues.',
        'Provide digital literacy training and resources.',
        'Organize workshops on safe online practices and cyber hygiene.',
        'Advocate for the protection of freedom of expression online.',
        'Support initiatives to improve access to the internet in underserved areas.',
        'Collaborate with tech companies to promote ethical data handling practices.',
        'Host events to educate the public on their digital rights and how to protect them.',
        'Promote tools and resources for secure communication and data protection.',
        'Engage in research and policy advocacy to address emerging digital rights issues.',
    ]
},

'Economic Empowerment': {
    'Objectives': [
        'Promote economic empowerment and entrepreneurship.',
        'Support initiatives for job creation and financial inclusion.',
    ],
    'Activities': [
        'Offer business development training and mentorship.',
        'Facilitate access to microloans or small business grants.',
        'Organize networking events and economic forums.',
        'Provide financial literacy workshops to enhance personal and business finance management.',
        'Support initiatives that promote women and minority entrepreneurship.',
        'Create and support incubators or accelerators for startups and small businesses.',
        'Partner with local businesses to offer apprenticeships or job placement programs.',
        'Advocate for policies that support economic development and job creation.',
        'Host career fairs and job readiness workshops to connect individuals with employment opportunities.',
        'Facilitate access to technology and resources for underserved entrepreneurs.',
    ]
},

'Policy Advocacy': {
    'Objectives': [
        'Advocate for policy changes and legislative reform.',
        'Promote public awareness and engagement in policy issues.',
    ],
    'Activities': [
        'Develop policy briefs and position papers.',
        'Engage with policymakers and government officials.',
        'Mobilize grassroots advocacy campaigns.',
        'Organize public forums and town hall meetings to discuss policy issues.',
        'Conduct research and analysis to support advocacy efforts.',
        'Create and disseminate educational materials to inform the public about policy issues.',
        'Build coalitions with other organizations to strengthen advocacy efforts.',
        'Host workshops and training sessions on effective advocacy strategies.',
        'Track and report on legislative developments and policy changes.'
    ]
},


'Artistic Advocacy': {
    'Objectives': [
        'Promote and support artistic expression and creativity for social causes.',
        'Provide platforms for artists to advocate for their causes through art.',
    ],
    'Activities': [
        'Organize art exhibitions and galleries focused on social issues.',
        'Conduct art workshops and classes that highlight advocacy.',
        'Fundraise for art supplies and resources for advocacy projects.',
        'Advocate for the importance of art in education and society.',
        'Host art-based fundraising events to support social causes.',
        'Collaborate with artists to create public art installations addressing social issues.',
        'Create and distribute art that raises awareness about specific causes.',
        'Support artist-in-residence programs that focus on community engagement and advocacy.',
        'Promote art as a tool for social change through public talks and panels.',
        'Develop partnerships with schools and community organizations to integrate art into social advocacy.'
    ]
},



    'Other': {
        'Objectives': [
        'Support miscellaneous causes or initiatives not covered by other categories.',
        ],
        'Activities': [
            'Tailor activities based on the specific nature of the campaign.',
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
    category = models.CharField(max_length=100, default='default_category')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(default=timezone.now)  # Use timezone.now() as default

    def __str__(self):
        return self.name



class CampaignFund(models.Model):
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paypal_email = models.EmailField(default="paypal_email")

    def progress_percentage(self):
        if self.target_amount > 0:
            return (self.amount_raised / self.target_amount) * 100
        return 0




class Donation(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donor_name = models.CharField(max_length=255, default="Anonymous")  # Set a default value
    transaction_id = models.CharField(max_length=255, unique=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)  # Automatically set the field to now when the donation is created

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Remove the fund update from here
        # This will prevent double counting





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
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="comments")
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



import re
from django.utils.html import escape


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(default='say something..')
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # If this is a new message
            # Convert plain text links to clickable links
            self.content = re.sub(
                r'(https?://\S+)', 
                r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', 
                self.content
            )

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
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when an instance is created

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



class ChangemakerAward(models.Model):
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'

    AWARD_CHOICES = (
        (BRONZE, 'Bronze'),
        (SILVER, 'Silver'),
        (GOLD, 'Gold'),
    )

    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='changemaker_awards')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='related_awards')
    award = models.CharField(max_length=6, choices=AWARD_CHOICES, default=BRONZE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.award}'

    @staticmethod
    def assign_award(user):
        """
        Assigns the appropriate award based on the number of campaigns the user has completed.
        """
        campaign_count = Campaign.objects.filter(user=user).count()
        
        if campaign_count >= 3:
            award = ChangemakerAward.GOLD
        elif campaign_count == 2:
            award = ChangemakerAward.SILVER
        else:
            award = ChangemakerAward.BRONZE

        # Get the most recent campaign for this user
        latest_campaign = Campaign.objects.filter(user=user).latest('timestamp')

        # Check if this user already has an award for this campaign
        if not ChangemakerAward.objects.filter(user=user, campaign=latest_campaign).exists():
            ChangemakerAward.objects.create(user=user, campaign=latest_campaign, award=award)

    @staticmethod
    def get_awards(user):
        """
        Returns the list of awards earned by the user.
        """
        return ChangemakerAward.objects.filter(user=user)


# marketing 
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    is_published = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


