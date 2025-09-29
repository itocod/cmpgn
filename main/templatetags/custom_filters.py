# main/templatetags/custom_filters.py
import re
from django import template
from django.db.models import Sum
from django.forms import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to a form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={"class": css_class})
    elif isinstance(field, str):
        # Handle string fields (like rendered radio buttons)
        return field
    else:
        # Fallback for other field types
        return field

@register.filter
def format_count(value):
    """
    Format numbers for display (e.g., 1000 becomes 1K)
    """
    try:
        value = int(value)
        if value >= 1000000:
            return f'{value/1000000:.1f}M'
        elif value >= 1000:
            return f'{value/1000:.1f}K'
        else:
            return str(value)
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def regex_replace(value, pattern):
    return re.sub(pattern, '', value)

@register.filter
def fulfilled_count(pledges):
    return pledges.filter(is_fulfilled=True).count()

@register.filter
def pending_count(pledges):
    return pledges.filter(is_fulfilled=False).count()

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def sum_pledges(pledges):
    return pledges.aggregate(total=Sum('amount'))['total'] or 0

@register.filter
def digits_only(value):
    """Remove all non-digit characters (for WhatsApp numbers)."""
    if not value:
        return ""
    return re.sub(r'[^0-9]', '', value)