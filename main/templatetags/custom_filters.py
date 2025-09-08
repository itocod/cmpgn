# main/templatetags/custom_filters.py
import re
from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})

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