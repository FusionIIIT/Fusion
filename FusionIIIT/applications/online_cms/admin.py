from django.contrib import admin

from .models import (Assignment, CourseDocuments, Forum,
                     ForumReply, Quiz, QuizQuestion, QuizResult, StudentAnswer,
                     StudentAssignment, Topics,
                    )
#need to register all the tables here which are functions in models.py
admin.site.register(CourseDocuments)

# admin.site.register(CourseVideo)

admin.site.register(Quiz)

admin.site.register(Topics)

admin.site.register(QuizQuestion)

admin.site.register(StudentAnswer)

admin.site.register(Assignment)

admin.site.register(StudentAssignment)

admin.site.register(QuizResult)

admin.site.register(Forum)

admin.site.register(ForumReply)
