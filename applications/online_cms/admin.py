from django.contrib import admin

from .models import (Assignment, CourseDocuments, CourseVideo, Forum,
                     ForumReply, Quiz, QuizQuestion, QuizResult, StudentAnswer,
                     StudentAssignment, Topics)

class QuizResultAdmin(admin.ModelAdmin):
    model = QuizResult
    raw_id_fields = ("student_id",)

admin.site.register(CourseDocuments)

admin.site.register(CourseVideo)

admin.site.register(Quiz)

admin.site.register(Topics)

admin.site.register(QuizQuestion)

admin.site.register(StudentAnswer)

admin.site.register(Assignment)

admin.site.register(StudentAssignment)

admin.site.register(QuizResult, QuizResultAdmin)

admin.site.register(Forum)

admin.site.register(ForumReply)
