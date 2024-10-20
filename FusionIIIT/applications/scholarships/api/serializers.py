from rest_framework import serializers
from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.scholarships.models import Award_and_scholarship,Previous_winner


class AwardAndScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award_and_scholarship
        fields = ['award_name', 'catalog']  


class PreviousWinnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Previous_winner
        fields = ['student', 'programme', 'year', 'award_id'] 



# class McmSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Mcm
#         fields = [
#             'brother_name', 'brother_occupation', 'sister_name', 'sister_occupation',
#             'income_father', 'income_mother', 'income_other', 'father_occ', 'mother_occ',
#             'father_occ_desc', 'mother_occ_desc', 'four_wheeler', 'four_wheeler_desc',
#             'two_wheeler', 'two_wheeler_desc', 'house', 'plot_area', 'constructed_area',
#             'school_fee', 'school_name', 'bank_name', 'loan_amount', 'college_fee',
#             'college_name', 'income_certificate', 'forms', 'status', 'student', 
#             'annual_income', 'date', 'award_id'
#         ]


# class NotionalPrizeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notional_prize
#         fields = ['spi', 'cpi', 'year', 'award_id']


# class ReleaseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Release
#         fields = [
#             'date_time', 'programme', 'startdate', 'enddate', 'award',
#             'remarks', 'batch', 'notif_visible'
#         ]

# class NotificationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notification
#         fields = [
#             'release_id', 'student_id', 'notification_mcm_flag', 
#             'notification_convocation_flag', 'invite_mcm_accept_flag', 
#             'invite_convocation_accept_flag'
#         ]

# class ApplicationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Application
#         fields = ['application_id', 'student_id', 'applied_flag', 'award']


# class DirectorSilverSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Director_silver
#         fields = [
#             'nearest_policestation', 'nearest_railwaystation', 'correspondence_address',
#             'student', 'award_id', 'award_type', 'status', 'relevant_document', 'date',
#             'financial_assistance', 'grand_total', 'inside_achievements', 'justification',
#             'outside_achievements'
#         ]



# class ProficiencyDmSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Proficiency_dm
#         fields = [
#             'relevant_document', 'title_name', 'student', 'award_id', 'award_type', 
#             'status', 'nearest_policestation', 'nearest_railwaystation', 
#             'correspondence_address', 'no_of_students', 'date', 'roll_no1', 'roll_no2', 
#             'roll_no3', 'roll_no4', 'roll_no5', 'financial_assistance', 
#             'brief_description', 'justification', 'grand_total', 'ece_topic', 'cse_topic', 
#             'mech_topic', 'design_topic', 'ece_percentage', 'cse_percentage', 
#             'mech_percentage', 'design_percentage'
#         ]


# class DirectorGoldSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Director_gold
#         fields = [
#             'student', 'status', 'correspondence_address', 'nearest_policestation', 
#             'nearest_railwaystation', 'relevant_document', 'date', 'award_id', 
#             'financial_assistance', 'academic_achievements', 'science_inside', 
#             'science_outside', 'games_inside', 'games_outside', 'cultural_inside', 
#             'cultural_outside', 'social', 'corporate', 'hall_activities', 
#             'gymkhana_activities', 'institute_activities', 'counselling_activities', 
#             'other_activities', 'justification', 'grand_total'
#         ]


