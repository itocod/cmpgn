import re
from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})

@register.filter
def format_count(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    if value >= 1_000_000_000:
        return f'{value / 1_000_000_000:.1f}B'
    elif value >= 1_000_000:
        return f'{value / 1_000_000:.1f}M'
    elif value >= 1_000:
        return f'{value / 1_000:.1f}K'
    return str(value)


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