from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allow dict[key] lookup in templates: {{ mydict|get_item:key }}"""
    if dictionary is None:
        return None
    # Checks for integer key first, falls back to string key if not found
    return dictionary.get(key) or dictionary.get(str(key))