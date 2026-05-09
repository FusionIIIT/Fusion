from rest_framework import serializers
from .models import (
    Messinfo, Mess_reg, MessBillBase, Monthly_bill, Payments, Menu,
    Rebate, Vacation_food, Nonveg_menu, Nonveg_data, Special_request,
    Mess_meeting, Mess_minutes, Feedback, RegistrationRequest,
    DeregistrationRequest, PaymentUpdateRequest, MenuPoll, MenuPollOption,
    MessAnnouncement,
)
from applications.academic_information.models import Student

class MessinfoSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Messinfo
        fields = '__all__'


class RegistrationRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = RegistrationRequest
        fields = '__all__'


class DeregistrationRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = DeregistrationRequest
        fields = '__all__'


class PaymentUpdateRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = PaymentUpdateRequest
        fields = '__all__'

class MessRegSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mess_reg
        fields = '__all__'

class MonthlyBillSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Monthly_bill
        fields = '__all__'

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'


class MenuPollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.SerializerMethodField()
    vote_percentage = serializers.SerializerMethodField()
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = MenuPollOption
        fields = ('id', 'option_text', 'display_order', 'vote_count',
                  'vote_percentage', 'is_selected')

    def _get_votes(self, obj):
        prefetched_votes = getattr(obj, '_prefetched_objects_cache', {}).get('votes')
        if prefetched_votes is not None:
            return list(prefetched_votes)
        return list(obj.votes.all())

    def get_vote_count(self, obj):
        return len(self._get_votes(obj))

    def get_vote_percentage(self, obj):
        total_votes = self.context.get('total_votes', 0) or 0
        if not total_votes:
            return 0
        return round((len(self._get_votes(obj)) * 100.0) / total_votes, 2)

    def get_is_selected(self, obj):
        return obj.id == self.context.get('selected_option_id')


class MenuPollSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    options = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    user_vote_option = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()
    meal_time_display = serializers.SerializerMethodField()
    mess_option_display = serializers.SerializerMethodField()

    class Meta:
        model = MenuPoll
        fields = (
            'id', 'question', 'description', 'mess_option',
            'mess_option_display', 'meal_time', 'meal_time_display',
            'poll_date', 'status', 'created_by', 'created_at', 'updated_at',
            'total_votes', 'user_vote_option', 'can_vote', 'options'
        )

    def _get_votes(self, obj):
        prefetched_votes = getattr(obj, '_prefetched_objects_cache', {}).get('votes')
        if prefetched_votes is not None:
            return list(prefetched_votes)
        return list(obj.votes.select_related('option', 'student_id'))

    def _get_selected_option_id(self, obj):
        student = self.context.get('student')
        if not student:
            return None

        for vote in self._get_votes(obj):
            if vote.student_id_id == student.pk:
                return vote.option_id
        return None

    def get_options(self, obj):
        total_votes = len(self._get_votes(obj))
        selected_option_id = self._get_selected_option_id(obj)
        serializer = MenuPollOptionSerializer(
            obj.options.all(),
            many=True,
            context={
                'selected_option_id': selected_option_id,
                'total_votes': total_votes,
            }
        )
        return serializer.data

    def get_total_votes(self, obj):
        return len(self._get_votes(obj))

    def get_user_vote_option(self, obj):
        return self._get_selected_option_id(obj)

    def get_can_vote(self, obj):
        student = self.context.get('student')
        student_mess_option = self.context.get('student_mess_option')
        return bool(student and obj.status == 'open' and
                    student_mess_option == obj.mess_option)

    def get_meal_time_display(self, obj):
        return obj.get_meal_time_display() if obj.meal_time else ''

    def get_mess_option_display(self, obj):
        return obj.get_mess_option_display()

class RebateSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Rebate
        fields = '__all__'

class VacationFoodSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Vacation_food
        fields = '__all__'

class NonvegMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nonveg_menu
        fields = '__all__'

class NonvegDataSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)
    dish = NonvegMenuSerializer(read_only=True)

    class Meta:
        model = Nonveg_data
        fields = '__all__'

class SpecialRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Special_request
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'

class MessMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mess_meeting
        fields = '__all__'

class MessMinutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mess_minutes
        fields = '__all__'

class PaymentsSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student_id.id.user.username', read_only=True)
    
    class Meta:
        model = Payments
        fields = '__all__'


class MessAnnouncementSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.username',
                                       read_only=True)

    class Meta:
        model = MessAnnouncement
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='id.user.username', read_only=True)
    first_name = serializers.CharField(source='id.user.first_name', read_only=True)
    last_name = serializers.CharField(source='id.user.last_name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'username', 'first_name', 'last_name', 'programme']


from rest_framework import serializers
from .models import VacationSurvey, VacationSurveyResponse

class VacationSurveySerializer(serializers.ModelSerializer):
    caretaker = serializers.CharField(source='caretaker.username', read_only=True)
    response_count = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    vacation_period = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = VacationSurvey
        fields = ('id', 'caretaker', 'start_date', 'end_date', 'description', 
                  'created_at', 'response_count', 'title', 'vacation_period')

    def get_response_count(self, obj):
        return obj.responses.count()

    def get_title(self, obj):
        desc = obj.description or ""
        if "|||" in desc:
            return desc.split("|||")[0]
        return "Vacation Survey"

    def get_vacation_period(self, obj):
        desc = obj.description or ""
        if "|||" in desc:
            parts = desc.split("|||")
            if len(parts) > 1:
                return parts[1]
        return f"{obj.start_date} to {obj.end_date}"

    def get_description(self, obj):
        desc = obj.description or ""
        if "|||" in desc:
            parts = desc.split("|||")
            if len(parts) > 2:
                return parts[2]
        return desc


class VacationSurveyResponseSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.id.user.username', read_only=True)
    student_name = serializers.SerializerMethodField()
    survey_details = serializers.SerializerMethodField()

    class Meta:
        model = VacationSurveyResponse
        fields = ('id', 'survey', 'student', 'student_id', 'student_name', 
                  'attending', 'details', 'response_date', 'survey_details')

    def get_student_name(self, obj):
        return f"{obj.student.id.user.first_name} {obj.student.id.user.last_name}"

    def get_survey_details(self, obj):
        return {
            'id': obj.survey.id,
            'start_date': obj.survey.start_date,
            'end_date': obj.survey.end_date,
            'description': obj.survey.description,
        }
