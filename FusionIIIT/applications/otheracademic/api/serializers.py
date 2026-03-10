from rest_framework import serializers
from applications.otheracademic.models import LeaveFormTable,BonafideFormTableUpdated

class LeaveFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveFormTable
        fields = '__all__'  


class BonafideFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonafideFormTableUpdated
        fields = [
            'student_names',
            'roll_nos',
            'branch_types',
            'semester_types',
            'purposes',
            'date_of_applications',
            'approve',
            'reject',
            'download_file'
        ]