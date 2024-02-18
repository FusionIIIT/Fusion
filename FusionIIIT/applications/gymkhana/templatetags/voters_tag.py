from django import template
import re
register = template.Library()

toggel = False

@register.simple_tag
def validate(user, groups):
    roll = user.username[:5] 
    branch = user.extrainfo.department.name
    if roll in groups:
        allowed_branches = groups[roll] 
        if 'All' in allowed_branches or branch in allowed_branches:
            return True
    return False
    
@register.simple_tag
def result():
    return toggel