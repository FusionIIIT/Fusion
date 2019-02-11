from django.contrib import admin

from .models import (AllTags, AnsweraQuestion, AskaQuestion, Comments, hidden,
                     report, tags)

admin.site.register(AskaQuestion)
admin.site.register(Comments)
admin.site.register(tags)
admin.site.register(hidden)
admin.site.register(AllTags)
admin.site.register(report)
admin.site.register(AnsweraQuestion)
