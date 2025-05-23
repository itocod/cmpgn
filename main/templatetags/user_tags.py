from django import template
from django.contrib.auth.models import User
from ..models import Follow

register = template.Library()

@register.filter(name='get_mutual_friends')
def get_mutual_friends(user, current_user):
    """Returns mutual friends between two users"""
    try:
        current_user_following = set(f.followed for f in current_user.following.all())
        user_following = set(f.followed for f in user.following.all())
        return current_user_following & user_following
    except Exception:
        return set()