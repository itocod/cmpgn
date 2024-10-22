from django import forms
from django.contrib.auth.models import User
from .models import Profile, Campaign, Comment, Activity, SupportCampaign, Chat, Message, Follow
from .models import   Brainstorming
from django.forms import inlineformset_factory

from .models import ActivityComment,CampaignProduct

from tinymce.widgets import TinyMCE
from .models import Report
from .models import NotInterested
from .models import Subscriber,Donation,CampaignFund

from django import forms
from .models import UserVerification


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




class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class CampaignProductForm(forms.ModelForm):
    class Meta:
        model = CampaignProduct
        fields = ['name', 'description', 'url', 'image',  'category', 'price', 'stock_quantity', 'is_active']






class ActivityCommentForm(forms.ModelForm):
    class Meta:
        model = ActivityComment
        fields = ['content']







class BrainstormingForm(forms.ModelForm):
    class Meta:
        model = Brainstorming
        fields = ['idea']  # Add other fields as needed





class ProfileSearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)

class CampaignSearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)


class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportCampaign
        fields = []  # Remove the 'category' field from the list




class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['content', 'file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

ActivityFormSet = inlineformset_factory(Campaign, Activity, form=ActivityForm, extra=1, can_delete=False)



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'username': 'Username:',
            'email': 'Email:'
        }




class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'contact', 'location', 'date_of_birth', 'gender', 'highest_level_of_education']
        labels = {
            'image': 'Profile Picture:',
            'bio': 'Bio:',
            'contact': 'Contact:',
            'location': 'Location:',
            'date_of_birth': 'Date of Birth:',
            'gender': 'Gender:',
            'highest_level_of_education': 'Highest Level of Education:',
            
        }




class CampaignForm(forms.ModelForm):
    emoji_shortcode = forms.CharField(max_length=50, required=False, label='Emoji Shortcut')
    
    class Meta:
        model = Campaign
        fields = ['title', 'content', 'poster', 'audio', 'visibility', 'category']
        labels = {
            'title': 'Title:',
            'content': 'Content:',
            'poster': 'Poster:',
            'audio': 'Audio:',
            'visibility': 'Visibility:',
            'category': 'Category:',

        }
    

class CampaignFundForm(forms.ModelForm):
    class Meta:
        model = CampaignFund
        fields = ['target_amount', 'paypal_email']
        labels = {
            'target_amount': 'Target Amount:',
            'paypal_email': 'PayPal Email:'
        }
        widgets = {
            'target_amount': forms.TextInput(attrs={
                'class': 'form-control',  
                'placeholder': 'Enter target amount'
            }),
            'paypal_email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter PayPal email'
            })
        }




class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['donor_name', 'amount']
        labels = {
            'donor_name': 'Your Name (optional):',
            'amount': 'Donation Amount:',
        }
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter donation amount'}),
        }








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


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']  # Include all fields that need to be submitted in the form

    def clean_attached_file(self):
        attached_file = self.cleaned_data.get('attached_file', False)
        if attached_file:
            # Check the file size or any other validation rules if needed
            # For example, you can limit the file size:
            max_size = 10 * 1024 * 1024  # 10 MB
            if attached_file.size > max_size:
                raise forms.ValidationError("File size too large. Please keep it under 10MB.")
        return attached_file

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
