from allauth.account.utils import user_email, user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This method is called just before a new social login is processed
        # If there's an account with the same email, connect the social account to it.
        email = sociallogin.user.email
        
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                # If the user exists, connect the social account to the existing user
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
