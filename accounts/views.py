
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from main.models import Profile 



from main.models import Campaign

def index(request):
    # Fetch all public campaigns
    public_campaigns = Campaign.objects.filter(visibility='public')  # Adjust this query to match your actual filtering criteria
    
    # Pass the public_campaigns to the template
    return render(request, 'accounts/index.html', {'public_campaigns': public_campaigns})



def home(request):
    # Your view logic here...
    return render(request, 'accounts/home.html', {})




def face(request):
    if request.user.is_authenticated:
        user_profile = get_object_or_404(Profile, user=request.user)
    else:
        user_profile = None  # Handle the case where the user is not authenticated or no profile is found

    context = {'user_profile': user_profile}
    return render(request, 'accounts/face.html', context)