
from django.shortcuts import render, redirect
from django.shortcuts import render, get_object_or_404
from main.models import Profile 




def index(request):
    # Your view logic here...
    return render(request, 'accounts/index.html', {})


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