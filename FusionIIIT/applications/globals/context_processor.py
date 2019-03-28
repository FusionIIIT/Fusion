from django.db.models import Q

from .models import HoldsDesignation


# def designation(request):
#     all_designation = HoldsDesignation.objects.exclude(designation__name='student')
#     designation_dictionary = {}
#     for i in all_designation:
#         key, value = str(i).split(' - ')
#         if key in designation_dictionary.keys():
#             designation_dictionary[key].append(value)
#         else:
#             designation_dictionary[key] = [value]
#     return {
#         'all_designation': designation_dictionary,
#     }

def designation(request):
    if request.user.is_authenticated():
        desig = HoldsDesignation.objects.filter(working=request.user)
        all_designation=[]
        for i in desig:
            all_designation.append(str(i.designation))
        print(all_designation)
        return {
            'all_designation': all_designation,
        }
    else:
        return {
            'all_designation': [],
        }
