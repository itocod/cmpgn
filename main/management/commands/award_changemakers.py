from django.core.management.base import BaseCommand
from main.models import Campaign, ChangemakerAward, Profile
from django.utils import timezone

class Command(BaseCommand):
    help = 'Find users who qualify for changemaker status and assign awards.'

    def handle(self, *args, **kwargs):
        # Find all users who have campaigns
        users = Profile.objects.all()
        
        for user in users:
            # Get all campaigns of the user
            user_campaigns = Campaign.objects.filter(user=user)

            changemaker_campaigns = []  # Will store campaigns that qualify for changemaker

            for campaign in user_campaigns:
                if campaign.is_changemaker:
                    changemaker_campaigns.append(campaign)

            # Check if the user qualifies for an award
            if changemaker_campaigns:
                campaign_count = len(changemaker_campaigns)
                
                if campaign_count >= 3:
                    award_type = ChangemakerAward.GOLD
                elif campaign_count == 2:
                    award_type = ChangemakerAward.SILVER
                else:
                    award_type = ChangemakerAward.BRONZE

                # Print the user and their campaigns for verification
                self.stdout.write(self.style.SUCCESS(
                    f'User: {user} - Campaigns: {[campaign.title for campaign in changemaker_campaigns]}'
                ))

                # Award the user if not already awarded for the latest campaign
                latest_campaign = changemaker_campaigns[-1]
                if not ChangemakerAward.objects.filter(user=user, campaign=latest_campaign).exists():
                    ChangemakerAward.objects.create(
                        user=user,
                        campaign=latest_campaign,
                        award=award_type,
                        timestamp=timezone.now()
                    )

                    self.stdout.write(self.style.SUCCESS(
                        f'Awarded {award_type} to {user} for campaign: {latest_campaign.title}'
                    ))
            else:
                self.stdout.write(self.style.WARNING(f'User: {user} does not qualify for changemaker status.'))


#python manage.py award_changemakers
