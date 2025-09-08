from django.core.management.base import BaseCommand
from main.models import Campaign, ChangemakerAward, Profile
from django.utils import timezone

class Command(BaseCommand):
    help = 'Find users who qualify for changemaker status and assign awards.'

    def handle(self, *args, **kwargs):
        users = Profile.objects.all()

        for user in users:
            user_campaigns = Campaign.objects.filter(user=user)
            changemaker_campaigns = [c for c in user_campaigns if c.is_changemaker]

            if changemaker_campaigns:
                campaign_count = len(changemaker_campaigns)
                
                # Determine award type
                if campaign_count >= 3:
                    award_type = ChangemakerAward.GOLD
                elif campaign_count == 2:
                    award_type = ChangemakerAward.SILVER
                else:
                    award_type = ChangemakerAward.BRONZE

                # Print user, campaigns, and award type BEFORE awarding
                self.stdout.write(self.style.SUCCESS(
                    f'User: {user} - Campaigns: {[c.title for c in changemaker_campaigns]} - '
                    f'Award Type: {award_type}'
                ))

                # Award the latest campaign if not already awarded
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

#python manage.py award_changemakers
