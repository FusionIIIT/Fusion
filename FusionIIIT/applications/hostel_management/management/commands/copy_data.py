from applications.academic_information.models import Student 
from applications.hostel_management.models import StudentDetails
from django.contrib.auth.models import User


def copy_data():
    
    # Fetch data from the Student table with a join to the User table
    student_data = Student.objects.all()

    # Iterate over the student data and create StudentDetails instances
    for student_instance in student_data:
        # Extract data from the related User instance
        id = student_instance.id_id
        user_instance = User.objects.filter(username=id).first();
        user_instance = User.objects.get(username=id)

        # Create a StudentDetails instance using data from the Student and User instances
        student_details_instance = StudentDetails(
            id=student_instance.id_id,
            first_name=user_instance.first_name,
            last_name=user_instance.last_name,
            programme=student_instance.programme,
            batch=student_instance.batch,
            room_num=student_instance.room_no,
            hall_no=student_instance.hall_no,
            specialization=student_instance.specialization,
            # parent_contact=student_instance.parent_contact,
            # address=student_instance.address
        )

        # Save the StudentDetails instance to the database
        student_details_instance.save()

# Call the function to initiate the data copying process
copy_data()
