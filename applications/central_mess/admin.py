from django.contrib import admin

from .models import (Feedback, Menu, Menu_change_request, Mess_meeting,
                     Mess_minutes, Mess_reg, Messinfo, Monthly_bill,
                     Nonveg_data, Nonveg_menu, Payments, Rebate,
                     Special_request, Vacation_food)

# Register your models here.


class MessinfoAdmin(admin.ModelAdmin):
    model = Messinfo
    fieldsets = [
        ('mess_option', {'fields': ['mess_option']}),
        ('student_id', {'fields': ['student_id']}),

    ]
    list_display = ('student_id', 'mess_option')


class Mess_minutesAdmin(admin.ModelAdmin):
    model = Mess_meeting
    fieldsets = [
        ('meeting_date', {'fields': ['meeting_date']}),
        ('mess_minutes', {'fields': ['mess_minutes']}),
        ]
    list_display = ('meeting_date', 'mess_minutes')



class MenuAdmin(admin.ModelAdmin):
    model = Menu
    fieldsets = [
        ('mess_option', {'fields': ['mess_option']}),
        ('meal_time', {'fields': ['meal_time']}),
        ('dish', {'fields': ['dish']}),
        ]
    list_display = ('mess_option', 'meal_time', 'dish')


class Mess_regAdmin(admin.ModelAdmin):
    model = Mess_reg
    fieldsets = [
        ('sem', {'fields': ['sem']}),
        ('start_reg', {'fields': ['start_reg']}),
        ('end_reg', {'fields': ['end_reg']}),
        ]
    list_display = ('start_reg', 'end_reg')



class Monthly_billAdmin(admin.ModelAdmin):
    model = Monthly_bill
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('month', {'fields': ['month']}),
        ('amount', {'fields': ['amount']}),
        ('nonveg_total_bill', {'fields': ['nonveg_total_bill']}),
        ('rebate_count', {'fields': ['rebate_count']}),
        ('rebate_amount', {'fields': ['rebate_amount']}),
        ('total_bill', {'fields': ['total_bill']}),

        ]
    list_display = ('student_id', 'month', 'amount',
                    'nonveg_total_bill', 'rebate_count', 'rebate_amount', 'total_bill')



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
    list_display = ('student_id', 'start_date', 'end_date',
                    'purpose', 'status')



class Vacation_foodAdmin(admin.ModelAdmin):
    model = Vacation_food
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('start_date', {'fields': ['start_date']}),
        ('end_date', {'fields': ['end_date']}),
        ('purpose', {'fields': ['purpose']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('student_id', 'start_date', 'end_date',
                    'purpose', 'status')



class Nonveg_menuAdmin(admin.ModelAdmin):
    model = Nonveg_menu
    fieldsets = [
        ('dish', {'fields': ['dish']}),
        ('price', {'fields': ['price']}),
        ('order_interval', {'fields': ['order_interval']}),
        ]
    list_display = ('dish', 'price', 'order_interval')



class Nonveg_dataAdmin(admin.ModelAdmin):
    model = Nonveg_data
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('order_date', {'fields': ['order_date']}),
        ('dish', {'fields': ['dish']}),
        ('order_interval', {'fields': ['order_interval']}),
        ]
    list_display = ('student_id', 'order_date', 'dish', 'order_interval')



class Special_requestAdmin(admin.ModelAdmin):
    model = Special_request
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('start_date', {'fields': ['start_date']}),
        ('end_date', {'fields': ['end_date']}),
        ('request', {'fields': ['request']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('student_id', 'start_date', 'end_date',
                    'request', 'status')



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
        ('meet_date', {'fields': ['meet_date']}),
        ('agenda', {'fields': ['agenda']}),
        ('venue', {'fields': ['venue']}),
        ('meeting_time', {'fields': ['meeting_time']}),
        ]
    list_display = ('meet_date', 'agenda', 'venue', 'meeting_time')



class FeedbackAdmin(admin.ModelAdmin):
    model = Feedback
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('fdate', {'fields': ['fdate']}),
        ('description', {'fields': ['description']}),
        ('feedback_type', {'fields': ['feedback_type']})
        ]
    list_display = ('student_id', 'fdate', 'description', 'feedback_type')


admin.site.register(Mess_minutes, Mess_minutesAdmin),
admin.site.register(Messinfo, MessinfoAdmin),
admin.site.register(Menu, MenuAdmin),
admin.site.register(Mess_reg, Mess_regAdmin),
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
