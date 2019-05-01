from django import template


register = template.Library()

@register.filter
def get_key(dictionary, key):
    return dictionary.get(key)
