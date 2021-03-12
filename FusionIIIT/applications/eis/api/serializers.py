from django.contrib.auth import get_user_model

from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.eis.models import (emp_research_papers,emp_published_books,emp_research_projects,
                                    emp_consultancy_projects,emp_patents,emp_techtransfer,emp_mtechphd_thesis,
                                    emp_visits,emp_confrence_organised,emp_achievement,
                                    emp_expert_lectures,emp_session_chair,emp_keynote_address,
                                    emp_event_organized,faculty_about)
from applications.globals.api.serializers import ExtraInfoSerializer, UserSerializer, HoldsDesignationSerializer

User = get_user_model()

class EmpResearchPapersSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_research_papers
        fields = ('__all__')

class EmpPublishedBooksSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_published_books
        fields = ('__all__')

class EmpResearchProjectsSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_research_projects
        fields = ('__all__')

class EmpConsultancyProjectsSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_consultancy_projects
        fields = ('__all__')

class EmpPatentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_patents
        fields = ('__all__')

class EmpTechTransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_techtransfer
        fields = ('__all__')

class EmpMtechPhdThesisSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_mtechphd_thesis
        fields = ('__all__')

class EmpVisitsSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_visits
        fields = ('__all__')

class EmpConfrenceOrganisedSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_confrence_organised
        fields = ('__all__')

class EmpAchievementSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_achievement
        fields = ('__all__')

class EmpExpertLecturesSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_expert_lectures
        fields = ('__all__')

class EmpSessionChairSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_session_chair
        fields = ('__all__')

class EmpKeynoteAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_keynote_address
        fields = ('__all__')

class EmpEventOrganizedSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_event_organized
        fields = ('__all__')

class FacultyAboutSerializer(serializers.ModelSerializer):

    class Meta:
        model = faculty_about
        fields = ('__all__')
