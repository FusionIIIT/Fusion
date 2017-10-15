from django.contrib import admin

from .models import (Feedback, Menu, Menu_change_request, Mess, Mess_meeting,
                     Monthly_bill, Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food)

# Register your models here.


class MessAdmin(admin.ModelAdmin):
    model = Mess
    fieldsets = [
        ('mess_option', {'fields': ['department']}),
        ('student', {'fields': ['sanction_cl_rh']}),
        ('nonveg_total_bill', {'fields': ['nonveg_total_bill']}),
        ('rebate_count', {'fields': ['rebate_count']}),
        ('count', {'fields': ['count']}),
        ('current_bill', {'fields': ['current_bill']})

    ]
    list_display = ('student', 'mess_option', 'nonveg_total_bill', 'rebate_count',
                    'count', 'current_bill')


class MenuAdmin(admin.ModelAdmin):
    model = Menu
    fieldsets = [
        ('mess_option', {'fields': ['mess_option']}),
        ('meal_time', {'fields': ['meal_time']}),
        ('dish', {'fields': ['dish']}),
        ]
    list_display = ('mess_option', 'meal_time', 'dish')


class Monthly_billAdmin(admin.ModelAdmin):
    model = Monthly_bill
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('month', {'fields': ['month']}),
        ('amount', {'fields': ['amount']}),
        ]
    list_display = ('student_id', 'month', 'amount')


class PaymentsAdmin(admin.ModelAdmin):
    model = Payments
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('sem', {'fields': ['sem']}),
        ('amount_paid', {'fields': ['amount_paid']}),
        ]
    list_display = ('student_id', 'sem', 'amount_paid')


class RebateAdmin(admin.ModelAdmin):
    model = Rebate
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('start_date', {'fields': ['start_date']}),
        ('end_date', {'fields': ['end_date']}),
        ('purpose', {'fields': ['purpose']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('student_id', 'start_date', 'end_date', 'purpose', 'status')


class Vacation_foodAdmin(admin.ModelAdmin):
    model = Vacation_food
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('start_date', {'fields': ['start_date']}),
        ('end_date', {'fields': ['end_date']}),
        ('purpose', {'fields': ['purpose']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('student_id', 'start_date', 'end_date', 'purpose', 'status')


class Nonveg_menuAdmin(admin.ModelAdmin):
    model = Nonveg_menu
    fieldsets = [
        ('dish', {'fields': ['dish']}),
        ('price', {'fields': ['price']})
        ]
    list_display = ('dish', 'price')


class Nonveg_dataAdmin(admin.ModelAdmin):
    model = Nonveg_data
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('order_date', {'fields': ['order_date']}),
        ('order_interval', {'fields': ['order_interval']}),
        ('dish', {'fields': ['dish']})
        ]
    list_display = ('student_id', 'order_date', 'order_interval', 'dish')


class Special_requestAdmin(admin.ModelAdmin):
    model = Special_request
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('start_date', {'fields': ['start_date']}),
        ('end_date', {'fields': ['end_date']}),
        ('request', {'fields': ['request']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('student_id', 'start_date', 'end_date', 'request', 'status')


class Menu_change_requestAdmin(admin.ModelAdmin):
    model = Menu_change_request
    fieldsets = [
        ('dish', {'fields': ['dish']}),
        ('request', {'fields': ['request']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('dish', 'request', 'status')


class Mess_meetingAdmin(admin.ModelAdmin):
    model = Mess_meeting
    fieldsets = [
        ('meeting_date', {'fields': ['meeting_date']}),
        ('agenda', {'fields': ['agenda']}),
        ('venue', {'fields': ['venue']}),
        ('meeting_time', {'fields': ['meeting_time']}),
        ('mess_minutes', {'fields': ['mess_minutes']}),
        ]
    list_display = ('meeting_date', 'agenda', 'venue', 'meeting_time', 'mess_minutes')


class FeedbackAdmin(admin.ModelAdmin):
    model = Feedback
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('fdate', {'fields': ['fdate']}),
        ('description', {'fields': ['description']}),
        ('feedback_type', {'fields': ['feedback_type']})
        ]
    list_display = ('student_id', 'fdate', 'description', 'feedback_type')


admin.site.register(Mess, MessAdmin),
admin.site.register(Menu, MenuAdmin),
admin.site.register(Monthly_bill, Monthly_billAdmin),
admin.site.register(Payments, PaymentsAdmin),
admin.site.register(Rebate, RebateAdmin),
admin.site.register(Vacation_food, Vacation_foodAdmin),
admin.site.register(Special_request, Special_requestAdmin),
admin.site.register(Nonveg_menu, Nonveg_menuAdmin),
admin.site.register(Nonveg_data, Nonveg_dataAdmin),
admin.site.register(Mess_meeting, Mess_meetingAdmin),
admin.site.register(Feedback, FeedbackAdmin),
admin.site.register(Menu_change_request, Menu_change_requestAdmin)
