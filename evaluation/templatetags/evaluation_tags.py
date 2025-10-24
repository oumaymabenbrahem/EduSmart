from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary with a default of None if key doesn't exist"""
    return dictionary.get(key, None)
