from django.contrib import admin

# Register your models here.
from .models import (Award_and_scholarship, Director_gold, Director_silver,
                     Mcm, Notional_prize, Previous_winner, DM_Proficiency_gold, IIITDM_Proficiency
                     Release,Notification,Application)

admin.site.register(Mcm),
admin.site.register(Award_and_scholarship),
admin.site.register(Previous_winner),
admin.site.register(Release),
admin.site.register(DM_Proficiency_gold),
admin.site.register(IIITDM_Proficiency),
admin.site.register(Director_silver),
admin.site.register(Director_gold),
admin.site.register(Notional_prize),
admin.site.register(Notification),
admin.site.register(Application),
