from rest_framework import serializers
from applications.hr2.models import LTCform, CPDAAdvanceform, CPDAReimbursementform, LeaveForm, Appraisalform, LeaveBalance


class LTC_serializer(serializers.ModelSerializer):
    class Meta:
        model = LTCform
        fields = [
            'id',
            'employeeId',
            'name',
            'blockYear',
            'pfNo',
            'basicPaySalary',
            'designation',
            'departmentInfo',
            'leaveRequired',
            'leaveStartDate',
            'leaveEndDate',
            'dateOfDepartureForFamily',
            'natureOfLeave',
            'purposeOfLeave',
            'hometownOrNot',
            'placeOfVisit',
            'addressDuringLeave',
            'modeofTravel',
            'detailsOfFamilyMembersAlreadyDone',
            'detailsOfFamilyMembersAboutToAvail',
            'detailsOfDependents',
            'amountOfAdvanceRequired',
            'certifiedThatFamilyDependents',
            'certifiedThatAdvanceTakenOn',
            'adjustedMonth',
            'submissionDate',
            'phoneNumberForContact',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        ]

    def create(self, validated_data):
        return LTCform.objects.create(**validated_data)


class CPDAAdvance_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAAdvanceform
        fields = [
            'id',
            'employeeId',
            'name',
            'designation',
            'pfNo',
            'purpose',
            'amountRequired',
            'advanceDueAdjustment',
            'submissionDate',
            'balanceAvailable',
            'advanceAmountPDA',
            'amountCheckedInPDA',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        ]

    def create(self, validated_data):
        return CPDAAdvanceform.objects.create(**validated_data)


class Appraisal_serializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisalform
        fields = [
            'id',
            'employeeId',
            'name',
            'designation',
            'disciplineInfo',
            'specificFieldOfKnowledge',
            'currentResearchInterests',
            'coursesTaught',
            'newCoursesIntroduced',
            'newCoursesDeveloped',
            'otherInstructionalTasks',
            'thesisSupervision',
            'sponsoredReseachProjects',
            'otherResearchElement',
            'publication',
            'referredConference',
            'conferenceOrganised',
            'membership',
            'honours',
            'editorOfPublications',
            'expertLectureDelivered',
            'membershipOfBOS',
            'otherExtensionTasks',
            'administrativeAssignment',
            'serviceToInstitute',
            'otherContribution',
            'performanceComments',
            'submissionDate',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        ]

    def create(self, validated_data):
        return Appraisalform.objects.create(**validated_data)


class CPDAReimbursement_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAReimbursementform
        fields = [
            'id',
            'employeeId',
            'name',
            'designation',
            'pfNo',
            'advanceTaken',
            'purpose',
            'adjustmentSubmitted',
            'balanceAvailable',
            'advanceDueAdjustment',
            'advanceAmountPDA',
            'amountCheckedInPDA',
            'submissionDate',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        ]

    def create(self, validated_data):
        return CPDAReimbursementform.objects.create(**validated_data)


class Leave_serializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveForm
        fields = [
            'id',
            'employeeId',
            'name',
            'designation',
            'submissionDate',
            'pfNo',
            'departmentInfo',
            'natureOfLeave',
            'leaveStartDate',
            'leaveEndDate',
            'purposeOfLeave',
            'addressDuringLeave',
            'academicResponsibility',
            'addministrativeResponsibiltyAssigned',
            'approved',
            'approvedDate',
            'created_by',
            'approved_by',
        ]

    def create(self, validated_data):
        return LeaveForm.objects.create(**validated_data)


class LeaveBalanace_serializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = [
            'id',
            'employeeId',
            'casualLeave',
            'specialCasualLeave',
            'earnedLeave',
            'commutedLeave',
            'restrictedHoliday',
            'stationLeave',
            'vacationLeave',
        ]

    def create(self, validated_data):
        return LeaveBalance.objects.create(**validated_data)
