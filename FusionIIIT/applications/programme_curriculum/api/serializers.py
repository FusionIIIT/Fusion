from rest_framework import serializers
from applications.programme_curriculum.models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, CourseInstructor

# this is for Programme model ....


class ProgrammeSerializer(serializers.ModelSerializer):
    discipline = serializers.SerializerMethodField()
    programmes = serializers.SerializerMethodField()

    def get_discipline(self, obj):
        disciplines = obj.get_discipline_objects.all()
        return ', '.join([discipline.name for discipline in disciplines])  # Join disciplines into a single string

    def get_programmes(self, obj):
        return obj.name

    class Meta:
        model = Programme
        fields = [ 'programmes', 'discipline']



# this is for Discipline ...
class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = "__all__"



# this is for Curriculum ....
# fields in fronted form --> name, version , batch , no of semester
class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['name', 'year']



class CurriculumBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = ['name', 'version', 'no_of_semester']

class CurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = ['name', 'version', 'batches', 'no_of_semester']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        batches = instance.batches.all()
        representations = []
        for batch in batches:
            batch_representation = {
                'name': representation['name'],
                'version': representation['version'],
                'no_of_semester': representation['no_of_semester'],
                'batch': f"{representation['name']} {batch.year}"
            }
            representations.append(batch_representation)
        return representations



class ProgrammeInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Programme
        fields = ['category', 'name', 'programme_begin_year']




# this is for Semester model ...
# no frontend form for this model ...
class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = "__all__"



# this is for course model ...
# fields in frontend form --> coursecode, coursename, credit         
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"



# this is for Batch model ...
# field in frontend form  --> name, discipline, year, curriculum .         
# class BatchSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Batch
#         fields = "__all__"


# for this 2 there is no frontend form ...


# CourseSlot model serializers ...
class CourseSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSlot
        fields = "__all__"



# CourseInstructor model serializers ...
class CourseInstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseInstructor
        fields = "__all__"


class ProgrammePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ['id', 'category', 'name', 'programme_begin_year']
