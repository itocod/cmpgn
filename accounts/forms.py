# forms.py
from django import forms
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    terms_agreement = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'You must agree to the terms and conditions to sign up.'
        }
    )

    def clean_terms_agreement(self):
        terms_agreed = self.cleaned_data.get('terms_agreement')
        if not terms_agreed:
            raise forms.ValidationError("You must agree to the terms and conditions.")
        return terms_agreed

    def save(self, request):
        user = super().save(request)
        # You can store the terms agreement date if needed
        # user.profile.terms_agreed = timezone.now()
        # user.profile.save()
        return user