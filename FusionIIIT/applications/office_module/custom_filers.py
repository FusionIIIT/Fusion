from django import template

@register.filter
def strip_double_quotes(quoted_string):
    return quoted_string.replace('"', '')