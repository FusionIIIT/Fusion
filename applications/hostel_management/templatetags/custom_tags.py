from django import template

register = template.Library()

def get_hall_no(value, args):
    # print("value ", value)
    # print("args ", args, type(args))
    args = str(args)
    # print("value.args ", value[args])
    return value[args]

register.filter('get_hall_no', get_hall_no)