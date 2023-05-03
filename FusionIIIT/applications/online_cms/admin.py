from django.contrib import admin

from .models import (Assignment, CourseDocuments, CourseVideo, Forum,
                     ForumReply, Quiz, QuizQuestion, QuizResult, StudentAnswer,
                     StudentAssignment1, Topics,CourseSlide,CourseAssignment
                     )

class QuizResultAdmin(admin.ModelAdmin):
    model = QuizResult
    raw_id_fields = ("student_id",)

admin.site.register(CourseDocuments)
admin.site.register(CourseSlide)
admin.site.register(CourseVideo)
admin.site.register(CourseAssignment)
admin.site.register(Quiz)

admin.site.register(Topics)

admin.site.register(QuizQuestion)

admin.site.register(StudentAnswer)

admin.site.register(Assignment)

admin.site.register(StudentAssignment1)

admin.site.register(QuizResult, QuizResultAdmin)

admin.site.register(Forum)

admin.site.register(ForumReply)
