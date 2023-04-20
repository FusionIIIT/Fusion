from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, Serializer, SerializerMetaclass
from applications.research_procedures.models import Patent,ResearchProject, ConsultancyProject
from applications.eis.models import (emp_research_papers,emp_published_books,emp_research_projects,
                                    emp_consultancy_projects,emp_patents,emp_techtransfer,emp_mtechphd_thesis,
                                    emp_visits,emp_confrence_organised,emp_achievement,
                                    emp_expert_lectures,emp_session_chair,emp_keynote_address,
                                    emp_event_organized,faculty_about)
from applications.globals.api.serializers import ExtraInfoSerializer, UserSerializer, HoldsDesignationSerializer

User = get_user_model()

class PatentSerializer(ModelSerializer):
    class Meta:
        model = Patent
        fields = '__all__'


class ResearchProjectSerializer(ModelSerializer):
    class Meta:      
        model = emp_research_projects
        fields = ('pf_no','pi','co_pi','title','funding_agency','financial_outlay','status','start_date','date_submission','finish_date')

class ConsultancyProjectSerializer(ModelSerializer):
    class Meta:
        model = emp_consultancy_projects
        fields = ('consultants','client','title','financial_outlay','pf_no','start_date','end_date')

class EmpResearchProjectsSerializer(serializers.ModelSerializer):

    class Meta:
        model = emp_research_projects
        fields = ('__all__')


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
