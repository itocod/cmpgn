from django import forms
from django.contrib.auth.models import User
from .models import Profile, Campaign, Comment, Activity, SupportCampaign, Chat, Message, Follow

from django.forms import inlineformset_factory

from .models import ActivityComment,CampaignProduct

from tinymce.widgets import TinyMCE
from .models import Report
from .models import NotInterested
from .models import Subscriber

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





from django import forms
from .models import CampaignProduct


from django import forms
from .models import CampaignProduct

class CampaignProductForm(forms.ModelForm):
    class Meta:
        model = CampaignProduct
        fields = ['name', 'description', 'image', 'price', 'stock_quantity', 'stock_status', 'is_active']






# ActivityCommentForm
class ActivityCommentForm(forms.ModelForm):
    class Meta:
        model = ActivityComment
        fields = ['content']

    def clean_content(self):
        content = self.cleaned_data.get('content')
        validate_no_long_words(content)  # Validate the content field
        return content



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






# forms.py
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 1,
                'placeholder': 'Type a message...',
                'id': 'messageInput'
            }),
            'file': forms.FileInput(attrs={
                'id': 'fileInput',
                'style': 'display: none;',
                'accept': 'image/*,.pdf,.doc,.docx,.txt'
            })
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

from django.core.exceptions import ValidationError
from PIL import Image
import os

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'title', 'category', 'poster', 'audio',
            'visibility', 'content', 'duration',
            'duration_unit', 'funding_goal'
        ]
        labels = {
            'title': 'Title:',
            'content': 'Content:',
            'poster': 'Poster:',
            'audio': 'Audio:',
            'visibility': 'Visibility:',
            'category': 'Category:',
            'duration': 'Duration:',
            'duration_unit': 'Duration Unit:',
            'funding_goal': 'Funding Goal (optional):',
        }

    def clean_poster(self):
        poster = self.cleaned_data.get('poster')
        if poster:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(poster.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("Unsupported file format. Allowed formats: JPG, JPEG, PNG, GIF, WEBP")

            try:
                image = Image.open(poster)
                image.verify()  # Check if it's a valid image file
            except Exception:
                raise ValidationError("Uploaded file is not a valid image.")

        return poster

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




from django import forms
from .models import Pledge

class PledgeForm(forms.ModelForm):
    class Meta:
        model = Pledge
        fields = ['campaign', 'amount', 'contact']
        widgets = {
            'campaign': forms.HiddenInput(),  # We'll typically set this in the view
            'amount': forms.NumberInput(attrs={
                'min': '1',
                'step': '0.01',
                'class': 'form-control'
            }),
           
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        campaign = kwargs.pop('campaign', None)
        super().__init__(*args, **kwargs)
        
        if campaign:
            self.initial['campaign'] = campaign
            self.fields['campaign'].widget = forms.HiddenInput()
        
        # Set minimum amount validation
        self.fields['amount'].min_value = 1




# forms.py
from django import forms
from .models import Donation

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'destination']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter donation amount',
                'step': '0.01',
                'min': '1'
            }),
            'destination': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'amount': 'Donation Amount',
            'destination': 'Where should your donation go?',
        }
