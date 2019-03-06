from django.contrib import admin

from .models import (Feedback, Menu, MenuChangeRequest, MessMeeting,
                     MessMinutes, MessRegistration, MessInformation, MonthlyBill,
                     NonVegData, NonVegMenu, Payments, Rebate,
                     SpecialRequest, VacationFood)

# Register your models here.


class MessinfoAdmin(admin.ModelAdmin):
    model = MessInformation
    fieldsets = [
        ('mess_option', {'fields': ['mess_option']}),
        ('student_id', {'fields': ['student_id']}),

    ]
    list_display = ('student_id', 'mess_option')


class Mess_minutesAdmin(admin.ModelAdmin):
    model = MessMeeting
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
    model = MessRegistration
    fieldsets = [
        ('sem', {'fields': ['sem']}),
        ('start_reg', {'fields': ['start_reg']}),
        ('end_reg', {'fields': ['end_reg']}),
        ]
    list_display = ('start_reg', 'end_reg')



class Monthly_billAdmin(admin.ModelAdmin):
    model = MonthlyBill
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('month', {'fields': ['month']}),
        ('year', {'fields': ['year']}),
        ('amount', {'fields': ['amount']}),
        ('nonveg_total_bill', {'fields': ['nonveg_total_bill']}),
        ('rebate_count', {'fields': ['rebate_count']}),
        ('rebate_amount', {'fields': ['rebate_amount']}),
        ('total_bill', {'fields': ['total_bill']}),

        ]
    list_display = ('student_id', 'month', 'year', 'amount',
                    'nonveg_total_bill', 'rebate_count', 'rebate_amount', 'total_bill')



class PaymentsAdmin(admin.ModelAdmin):
    model = Payments
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('sem', {'fields': ['sem']}),
        ('year', {'fields': ['year']}),
        ('amount_paid', {'fields': ['amount_paid']}),
        ]
    list_display = ('student_id', 'sem', 'year', 'amount_paid')


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
    model = VacationFood
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
    model = NonVegMenu
    fieldsets = [
        ('dish', {'fields': ['dish']}),
        ('price', {'fields': ['price']}),
        ('order_interval', {'fields': ['order_interval']}),
        ]
    list_display = ('dish', 'price', 'order_interval')



class Nonveg_dataAdmin(admin.ModelAdmin):
    model = NonVegData
    fieldsets = [
        ('student_id', {'fields': ['student_id']}),
        ('order_date', {'fields': ['order_date']}),
        ('dish', {'fields': ['dish']}),
        ('order_interval', {'fields': ['order_interval']}),
        ]
    list_display = ('student_id', 'order_date', 'dish', 'order_interval')



class Special_requestAdmin(admin.ModelAdmin):
    model = SpecialRequest
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
    model = MenuChangeRequest
    fieldsets = [
        ('dish', {'fields': ['dish']}),
        ('request', {'fields': ['request']}),
        ('status', {'fields': ['status']}),
        ]
    list_display = ('dish', 'request', 'status')


class Mess_meetingAdmin(admin.ModelAdmin):
    model = MessMeeting
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


admin.site.register(MessMinutes, Mess_minutesAdmin),
admin.site.register(MessInformation, MessinfoAdmin),
admin.site.register(Menu, MenuAdmin),
admin.site.register(MessRegistration, Mess_regAdmin),
admin.site.register(MonthlyBill, Monthly_billAdmin),
admin.site.register(Payments, PaymentsAdmin),
admin.site.register(Rebate, RebateAdmin),
admin.site.register(VacationFood, Vacation_foodAdmin),
admin.site.register(SpecialRequest, Special_requestAdmin),
admin.site.register(NonVegMenu, Nonveg_menuAdmin),
admin.site.register(NonVegData, Nonveg_dataAdmin),
admin.site.register(MessMeeting, Mess_meetingAdmin),
admin.site.register(Feedback, FeedbackAdmin),
admin.site.register(MenuChangeRequest, Menu_change_requestAdmin)
