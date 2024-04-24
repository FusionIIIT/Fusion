from rest_framework.authtoken.models import Token
from rest_framework import serializers

from applications.academic_procedures.models import (ThesisTopicProcess, InitialRegistrations,
                                                     FinalRegistrations, SemesterMarks,
                                                     BranchChange)

from applications.academic_information.api.serializers import (CurriculumInstructorSerializer,
                                                               CurriculumSerializer)
from applications.globals.api.serializers import (UserSerializer, HoldsDesignationSerializer)

class ThesisTopicProcessSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThesisTopicProcess
        fields = ('__all__')

class InitialRegistrationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = InitialRegistrations
        fields = ('__all__')

class FinalRegistrationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinalRegistrations
        fields = ('__all__')

class SemesterMarksSerializer(serializers.ModelSerializer):

    class Meta:
        model = SemesterMarks
        fields = ('__all__')

class BranchChangeSerializer(serializers.ModelSerializer):

    class Meta:
        model = BranchChange
        fields = ('__all__')
