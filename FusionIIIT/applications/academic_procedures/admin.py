from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (BranchChange, CoursesMtech, FeePayments, FinalRegistration, InitialRegistration,StudentRegistrationChecks,
                     MinimumCredits, Register, Thesis, CourseRequested,
                     ThesisTopicProcess, FeePayment, TeachingCreditRegistration,
                     SemesterMarks, MarkSubmissionCheck,Dues,MTechGraduateSeminarReport,PhDProgressExamination,AssistantshipClaim,MessDue,Assistantship_status, course_registration,
                     ThesisSubmission, ReviewInvitation)

class RegisterAdmin(admin.ModelAdmin):
    model = Register
    search_fields = ('curr_id__course_code',)


@admin.register(ThesisSubmission)
class ThesisSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_thesis_title', 'get_student', 'status', 'submitted_at', 'supervisor_approval', 'director_approval']
    list_filter = ['status', 'submitted_at', 'supervisor_approved_at', 'director_approved_at']
    search_fields = ['thesis__research_theme', 'thesis__student__id__user__username', 'thesis__student__id__user__first_name', 'thesis__student__id__user__last_name']
    readonly_fields = ['file_token', 'submitted_at', 'updated_at', 'get_synopsis_link', 'get_report_link']
    date_hierarchy = 'submitted_at'
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('thesis', 'status', 'file_token')
        }),
        ('Files', {
            'fields': ('synopsis', 'get_synopsis_link', 'thesis_report', 'get_report_link')
        }),
        ('Approvals', {
            'fields': ('supervisor', 'supervisor_approved_at', 'director', 'director_approved_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_thesis_title(self, obj):
        return obj.thesis.research_theme
    get_thesis_title.short_description = 'Thesis Title'
    get_thesis_title.admin_order_field = 'thesis__research_theme'
    
    def get_student(self, obj):
        if obj.thesis and obj.thesis.student:
            return obj.thesis.student.id.user.get_full_name() or obj.thesis.student.id.user.username
        return '-'
    get_student.short_description = 'Student'
    
    def supervisor_approval(self, obj):
        if obj.supervisor_approved_at:
            return format_html('<span style="color: green;">✓ {}</span>', obj.supervisor_approved_at.strftime('%Y-%m-%d'))
        return format_html('<span style="color: orange;">Pending</span>')
    supervisor_approval.short_description = 'Supervisor'
    
    def director_approval(self, obj):
        if obj.director_approved_at:
            return format_html('<span style="color: green;">✓ {}</span>', obj.director_approved_at.strftime('%Y-%m-%d'))
        return format_html('<span style="color: orange;">Pending</span>')
    director_approval.short_description = 'Director'
    
    def get_synopsis_link(self, obj):
        if obj.synopsis:
            return format_html('<a href="{}" target="_blank">View Synopsis</a>', obj.synopsis.url)
        return '-'
    get_synopsis_link.short_description = 'Synopsis Link'
    
    def get_report_link(self, obj):
        if obj.thesis_report:
            return format_html('<a href="{}" target="_blank">View Report</a>', obj.thesis_report.url)
        return '-'
    get_report_link.short_description = 'Report Link'


@admin.register(ReviewInvitation)
class ReviewInvitationAdmin(admin.ModelAdmin):
    list_display = ['id', 'prof_name', 'prof_email', 'get_thesis', 'status', 'priority', 'last_sent', 'expires_at', 'is_expired_badge']
    list_filter = ['status', 'priority', 'created_at', 'expires_at']
    search_fields = ['prof_name', 'prof_email', 'submission__thesis__research_theme']
    readonly_fields = ['token', 'created_at', 'updated_at', 'get_accept_url', 'get_reject_url', 'get_review_url']
    date_hierarchy = 'created_at'
    ordering = ['submission', 'priority']
    actions = ['resend_invitation', 'mark_expired', 'send_review_form']
    
    fieldsets = (
        ('Professor Information', {
            'fields': ('prof_name', 'prof_position', 'prof_email', 'prof_phone', 'prof_address', 'prof_time_ranking')
        }),
        ('Invitation Details', {
            'fields': ('submission', 'priority', 'token', 'status')
        }),
        ('Action URLs', {
            'fields': ('get_accept_url', 'get_reject_url', 'get_review_url'),
            'classes': ('collapse',)
        }),
        ('Email Tracking', {
            'fields': ('last_sent', 'review_form_sent', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_thesis(self, obj):
        return obj.submission.thesis.research_theme
    get_thesis.short_description = 'Thesis'
    get_thesis.admin_order_field = 'submission__thesis__research_theme'
    
    def is_expired_badge(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red; font-weight: bold;">EXPIRED</span>')
        elif obj.expires_at:
            days_left = (obj.expires_at - timezone.now()).days
            if days_left <= 7:
                return format_html('<span style="color: orange;">{} days left</span>', days_left)
            return format_html('<span style="color: green;">{} days left</span>', days_left)
        return '-'
    is_expired_badge.short_description = 'Expiry Status'
    
    def get_accept_url(self, obj):
        from django.conf import settings
        url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        url += reverse('procedures:invitation_action', args=[obj.token, 'accept'])
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    get_accept_url.short_description = 'Accept URL'
    
    def get_reject_url(self, obj):
        from django.conf import settings
        url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        url += reverse('procedures:invitation_action', args=[obj.token, 'reject'])
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    get_reject_url.short_description = 'Reject URL'
    
    def get_review_url(self, obj):
        from django.conf import settings
        url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        url += reverse('procedures:review_detail', args=[obj.token])
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    get_review_url.short_description = 'Review Form URL'
    
    def resend_invitation(self, request, queryset):
        from .utils import send_invitation_email
        count = 0
        for inv in queryset:
            if inv.status == 'pending' and not inv.is_expired():
                try:
                    send_invitation_email(inv)
                    inv.last_sent = timezone.now()
                    inv.save(update_fields=['last_sent'])
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Failed to send to {inv.prof_email}: {str(e)}", level='error')
        self.message_user(request, f"Successfully resent {count} invitation(s)")
    resend_invitation.short_description = "Resend invitation email to selected reviewers"
    
    def mark_expired(self, request, queryset):
        count = queryset.filter(status='pending').update(status='expired')
        self.message_user(request, f"Marked {count} invitation(s) as expired")
    mark_expired.short_description = "Mark selected invitations as expired"
    
    def send_review_form(self, request, queryset):
        from .utils import send_review_form_email
        count = 0
        for inv in queryset:
            if inv.status == 'accepted':
                try:
                    send_review_form_email(inv)
                    inv.review_form_sent = timezone.now()
                    inv.save(update_fields=['review_form_sent'])
                    count += 1
                except Exception as e:
                    self.message_user(request, f"Failed to send to {inv.prof_email}: {str(e)}", level='error')
        self.message_user(request, f"Successfully sent review form to {count} reviewer(s)")
    send_review_form.short_description = "Send review form email to accepted reviewers"


admin.site.register(Thesis)
admin.site.register(Register,RegisterAdmin)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
admin.site.register(MinimumCredits)
admin.site.register(ThesisTopicProcess)
admin.site.register(FeePayment)
admin.site.register(TeachingCreditRegistration)
admin.site.register(SemesterMarks)
admin.site.register(MarkSubmissionCheck)
admin.site.register(Dues)
admin.site.register(AssistantshipClaim)
admin.site.register(PhDProgressExamination)
admin.site.register(MTechGraduateSeminarReport)
admin.site.register(MessDue)
admin.site.register(Assistantship_status)
admin.site.register(FeePayments)
admin.site.register(CourseRequested)
admin.site.register(InitialRegistration)
admin.site.register(FinalRegistration)
admin.site.register(StudentRegistrationChecks)
admin.site.register(course_registration)

