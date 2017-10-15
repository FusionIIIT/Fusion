from django.contrib import admin

<<<<<<< HEAD
from .models import Register


admin.site.register(Register)
=======
from .models import FinalRegistrations, Register, Thesis

admin.site.register(Thesis)
admin.site.register(Register)
admin.site.register(FinalRegistrations)
>>>>>>> upstream/master
