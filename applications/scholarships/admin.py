from django.contrib import admin

# Register your models here.
from .models import (Award_and_scholarship, Director_gold, Director_silver,
                     Mcm, Notional_prize, Previous_winner, Proficiency_dm,
                     Release)

admin.site.register(Mcm),
admin.site.register(Award_and_scholarship),
admin.site.register(Previous_winner),
admin.site.register(Release),
admin.site.register(Proficiency_dm),
admin.site.register(Director_silver),
admin.site.register(Director_gold),
admin.site.register(Notional_prize),
