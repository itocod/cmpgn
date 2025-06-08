from django import forms
from django.contrib.auth.models import User
from .models import Profile, Campaign, Comment, Activity, SupportCampaign, Chat, Message, Follow
from .models import   Brainstorming
from django.forms import inlineformset_factory

from .models import ActivityComment,CampaignProduct

from tinymce.widgets import TinyMCE
from .models import Report
from .models import NotInterested
from .models import Subscriber,Donation

from django.core.exceptions import ValidationError
from django import forms
from .models import UserVerification




# Custom validator to check for long words
def validate_no_long_words(value):
    for word in value.split():
        if len(word) > 20:  # Check if any word exceeds 20 characters
            raise ValidationError(f"Word '{word}' exceeds the allowed length of 20 characters.")

# ReportForm
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_reason(self):
        reason = self.cleaned_data.get('reason')
        validate_no_long_words(reason)  # Validate the reason field
        return reason

    def clean_description(self):
        description = self.cleaned_data.get('description')
        validate_no_long_words(description)  # Validate the description field
        return description


# CampaignProductForm
class CampaignProductForm(forms.ModelForm):
    class Meta:
        model = CampaignProduct
        fields = ['name', 'description', 'url', 'image', 'category', 'price', 'stock_quantity', 'is_active']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        validate_no_long_words(name)  # Validate the name field
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        validate_no_long_words(description)  # Validate the description field
        return description


# ActivityCommentForm
class ActivityCommentForm(forms.ModelForm):
    class Meta:
        model = ActivityComment
        fields = ['content']

    def clean_content(self):
        content = self.cleaned_data.get('content')
        validate_no_long_words(content)  # Validate the content field
        return content


# BrainstormingForm

class BrainstormingForm(forms.ModelForm):
    class Meta:
        model = Brainstorming
        fields = ['idea', 'attachment']  # Added attachment field


# ActivityForm
class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'custom-textarea-{{ form.content.auto_id }}', 'rows': 3}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        validate_no_long_words(content)  # Validate the content field
        return content


ActivityFormSet = inlineformset_factory(Campaign, Activity, form=ActivityForm, extra=1, can_delete=False)


# ProfileForm
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'contact', 'location', 'date_of_birth', 'gender', 'highest_level_of_education']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-textarea'}),
            'contact': forms.TextInput(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'highest_level_of_education': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        validate_no_long_words(bio)  # Validate the bio field
        return bio

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        validate_no_long_words(contact)  # Validate the contact field
        return contact

    def clean_location(self):
        location = self.cleaned_data.get('location')
        validate_no_long_words(location)  # Validate the location field
        return location





from django_summernote.widgets import SummernoteWidget  # Alternative rich editor

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'quill-editor'}),
        }





# CommentForm
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

    def clean_text(self):
        text = self.cleaned_data.get('text')
        validate_no_long_words(text)  # Validate the text field
        return text




class UserVerificationForm(forms.ModelForm):
    class Meta:
        model = UserVerification
        fields = ['document_type', 'document']  # Exclude the user field

        widgets = {
            'document_type': forms.Select(attrs={'class': 'custom-select'}),
            'document': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
        }
    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            # You can add validation logic here, e.g., checking file type or size
            if document.size > 5 * 1024 * 1024:  # Example: limit file size to 5 MB
                raise forms.ValidationError("File size must be under 5 MB.")
        return document

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.user = user  # Set the user from the view
        if commit:
            instance.save()
        return instance



class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'required': True,
                'style': 'padding: 10px; width: 100%; box-sizing: border-box;'
            })
        }







class VerificationRequestForm(forms.Form):
    # You can include additional fields if needed
    message = forms.CharField(widget=forms.Textarea)

class VerificationReviewForm(forms.Form):
    # You can include additional fields if needed
    approval_status = forms.ChoiceField(choices=[(True, 'Approve'), (False, 'Deny')])
    review_comment = forms.CharField(widget=forms.Textarea, required=False)




class NotInterestedForm(forms.ModelForm):
    class Meta:
        model = NotInterested
        fields = ['campaign']











class ProfileSearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)

class CampaignSearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)


class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportCampaign
        fields = []  # Remove the 'category' field from the list





class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Username:',
            'email': 'Email:'
        }





# Custom validator to check for long words
def validate_no_long_words(value):
    for word in value.split():
        if len(word) > 20:  # Check if any word exceeds 20 characters
            raise ValidationError(f"Word '{word}' exceeds the allowed length of 20 characters.")

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ['title', 'category', 'poster', 'audio', 'visibility', 'content', 'target_amount','duration', 'duration_unit']
        labels = {
            'title': 'Title:',
            'content': 'Content:',
            'poster': 'Poster:',
            'audio': 'Audio:',
            'visibility': 'Visibility:',
            'category': 'Category:',
            'duration': 'Duration:',
            'duration_unit': 'Duration Unit:',
            'target_amount':'target_amount',
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['readonly'] = False  # Allow editing

    def clean_title(self):
        title = self.cleaned_data.get('title')
        validate_no_long_words(title)  # Validate the title field
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        validate_no_long_words(content)  # Validate the content field
        return content





from django import forms
from decimal import Decimal

# forms.py
class DonationForm(forms.Form):
    amount = forms.DecimalField(min_value=1.00, max_digits=10, decimal_places=2)
    tip_for_platform = forms.DecimalField(
        required=False,
        initial=0.00,
        min_value=0.00,
        max_digits=10,
        decimal_places=2,
        label="Tip for Platform (Optional)"
    )

    def __init__(self, *args, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.campaign = campaign

    def clean(self):
        cleaned_data = super().clean()
        if self.campaign and not self.campaign.stripe_connected_account_id:
            raise forms.ValidationError(
                "This campaign cannot accept donations yet because the owner hasn't connected a payment account. "
                "Please contact the campaign owner or support."
            )
        return cleaned_data




    


class ChatForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(queryset=None, widget=forms.CheckboxSelectMultiple)
    
    class Meta:
        model = Chat
        fields = ('title', 'participants',)

    def __init__(self, user, *args, **kwargs):
        super(ChatForm, self).__init__(*args, **kwargs)
        
        # Get the current user's followers and followings
        followers = Follow.objects.filter(followed=user)
        followings = Follow.objects.filter(follower=user)
        
        # Create a list of followers and followings
        user_choices = [(follower.follower.pk, follower.follower.username) for follower in followers] + \
                       [(following.followed.pk, following.followed.username) for following in followings]
        
        # Set the queryset for the participants field
        self.fields['participants'].queryset = User.objects.filter(pk__in=[choice[0] for choice in user_choices])




class UpdateVisibilityForm(forms.ModelForm):
    followers_visibility = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select followers to view"
    )

    class Meta:
        model = Campaign
        fields = ['visibility', 'followers_visibility']

    def __init__(self, *args, **kwargs):
        followers = kwargs.pop('followers', None)
        super().__init__(*args, **kwargs)

        if followers:
            self.fields['followers_visibility'].queryset = followers
