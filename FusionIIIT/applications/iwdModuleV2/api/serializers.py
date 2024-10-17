from rest_framework import serializers
from applications.iwdModuleV2.models import *

class PageOneDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageOneDetails
        fields = '__all__'


class PageTwoDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTwoDetails
        fields = '__all__'


class PageThreeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageThreeDetails
        fields = '__all__'


class AESDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AESDetails
        fields = '__all__'


class CorrigendumTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrigendumTable
        fields = '__all__'


class AddendumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addendum
        fields = '__all__'


class PreBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreBidDetails
        fields = '__all__'


class NoOfTechnicalBidTimesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoOfTechnicalBidTimes
        fields = '__all__'


class TechnicalBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalBidDetails
        fields = '__all__'


class TechnicalBidContractorDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalBidContractorDetails
        fields = '__all__'


class FinancialBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialBidDetails
        fields = '__all__'


class FinancialContractorDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialContractorDetails
        fields = '__all__'


class LetterOfIntentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterOfIntentDetails
        fields = '__all__'


class WorkOrderFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderForm
        fields = '__all__'


class AgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = '__all__'


class MilestonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestones
        fields = '__all__'


class ExtensionOfTimeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtensionOfTimeDetails
        fields = '__all__'


class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = '__all__'


class WorkOrderFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderForm
        fields = '__all__'  # or list specific fields here

class AgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = '__all__'  # or list specific fields here

class MilestonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestones
        fields = '__all__'  # or list specific fields here

class PageThreeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageThreeDetails
        fields = '__all__'  # or list specific fields here

class ExtensionOfTimeDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtensionOfTimeDetails
        fields = '__all__'  # or list specific fields here

class AESDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AESDetails
        fields = '__all__'  # or list specific fields here

class FinancialBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialBidDetails
        fields = '__all__'  # or list specific fields here

class TechnicalBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalBidDetails
        fields = '__all__'  # or list specific fields here

class FinancialContractorDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialContractorDetails
        fields = '__all__'  # or list specific fields here

class TechnicalBidContractorDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalBidContractorDetails
        fields = '__all__'  # or list specific fields here

class PreBidDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreBidDetails
        fields = '__all__'  # or list specific fields here

class CorrigendumTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrigendumTable
        fields = '__all__'  # or list specific fields here

class AddendumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addendum
        fields = '__all__'  # or list specific fields here

class LetterOfIntentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterOfIntentDetails
        fields = '__all__'  # or list specific fields here

class PageOneDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageOneDetails
        fields = '__all__'  # or list specific fields here

class PageTwoDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTwoDetails
        fields = '__all__'  # or list specific fields here