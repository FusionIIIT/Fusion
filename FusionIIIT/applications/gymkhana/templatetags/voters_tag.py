from django import template
import re
register = template.Library()

toggel = False

## A tag function to find whether to show the poll to the user or not
@register.simple_tag
def validate(user, groups):
    
    roll = user.username[:4]
    branch = user.extrainfo.department.name
    print(groups)
    if roll in groups.keys():
        if groups[roll][0] == 'All':
            return True
        else:
            if branch in groups[roll]:
                return  True
            else:
                return  False
    else:
        return False
    
@register.simple_tag
def result():
    return toggel