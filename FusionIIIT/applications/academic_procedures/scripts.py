from django.db import transaction

def temppp(cod,name,l,t,p,c,discipline_code,ins_code,year):
    discipline=Discipline.objects.get(acronym=discipline_code)
    user=User.objects.get(username=ins_code)
    teacher = ExtraInfo.objects.get(user=user)
    course=Courses.objects.get(code=cod,name=name)
    # course.disciplines.set(discipline)
    # cse=Discipline.objects.get(acronym='CSE')
    # ece=Discipline.objects.get(acronym='ECE')
    # me=Discipline.objects.get(acronym='ME')
    bcse = Batch.objects.filter(year=year,discipline=discipline).first()
    # bece = Batch.objects.filter(year=year,discipline=ece).first()
    # bme = Batch.objects.filter(year=year,discipline=me).first()
    
    CourseInstructor.objects.create(course_id=course,instructor_id=teacher,batch_id=bcse)
    # CourseInstructor.objects.create(course_id=course,instructor_id=teacher,batch_id=bme)
    # CourseInstructor.objects.create(course_id=course,instructor_id=teacher,batch_id=bece
    # 
@login_required
def add_new_profile (request):
    """
    To add details of new upcoming students in the database.User must be logged in and must be acadadmin

    @param:
        request - contains metadata about the requested page.

    @variables:
        profiles - gets the excel file having data
        excel - excel file
        sheet - sheet no in excel file
        roll_no - details of student from file
        first_name - details of student from file
        last_name - details of student from file
        email - details of student from file
        sex - details of student from file
        title - details of student from file
        dob - details of student from file
        fathers_name - details of student from file
        mothers_name - details of student from file
        category - details of student from file
        phone_no - details of student from file
        address - details of student from file
        department - details of student from file
        specialization - details of student from file
        hall_no - details of student from file
        programme - details of student from file
        batch - details of student from file
        user - new user created in database
        einfo - new extrainfo object created in database
        stud_data - new student object created in database
        desig - get designation object of student
        holds_desig - get hold_desig object of student
        currs - get curriculum details
        reg - create registeration object in registeration table

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context= {
        'tab_id' :['2','1']
    }
    if request.method == 'POST' and request.FILES:
        profiles=request.FILES['profiles']
        excel = xlrd.open_workbook(file_contents=profiles.read())
        sheet=excel.sheet_by_index(0)
        for i in range(sheet.nrows):
            code=str(sheet.cell(i,0).value)
            name=str(sheet.cell(i,1).value)
            l,t,p,c=str(sheet.cell(i,2).value).split('-')
            discipline_code=str(sheet.cell(i,3).value)
            ins_code=str(sheet.cell(i,4).value)
            year=int(sheet.cell(i,5).value)
            l = int(l)
            t = int(t)
            p = int(p)
            c = int(c)

            try:
                with transaction.atomic():
                    temppp(code,name,l,t,p,c,discipline_code,ins_code,year)
            except Exception as e:
                print(">>>>>>>",code,e)
            

            
    else:
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)

from django.db import transaction

def temppp(type, slot, sems, courses):
    sem_ids = list(map(int,sems.split('-')))
    course_codes = courses.split('-')
    s1 = []
    crs_list = []
    for crs in course_codes:
        crs_list.append(Courses.objects.get(code=crs))
    for s in sem_ids:
        s_id = Semester.objects.get(pk=s)
        temp = CourseSlot.objects.create(type=type,name=slot,semester=s_id)
        temp.courses.set(crs_list)

    
@login_required
def add_new_profile (request):
    """
    To add details of new upcoming students in the database.User must be logged in and must be acadadmin

    @param:
        request - contains metadata about the requested page.

    @variables:
        profiles - gets the excel file having data
        excel - excel file
        sheet - sheet no in excel file
        roll_no - details of student from file
        first_name - details of student from file
        last_name - details of student from file
        email - details of student from file
        sex - details of student from file
        title - details of student from file
        dob - details of student from file
        fathers_name - details of student from file
        mothers_name - details of student from file
        category - details of student from file
        phone_no - details of student from file
        address - details of student from file
        department - details of student from file
        specialization - details of student from file
        hall_no - details of student from file
        programme - details of student from file
        batch - details of student from file
        user - new user created in database
        einfo - new extrainfo object created in database
        stud_data - new student object created in database
        desig - get designation object of student
        holds_desig - get hold_desig object of student
        currs - get curriculum details
        reg - create registeration object in registeration table

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context= {
        'tab_id' :['2','1']
    }
    if request.method == 'POST' and request.FILES:
        profiles=request.FILES['profiles']
        excel = xlrd.open_workbook(file_contents=profiles.read())
        sheet=excel.sheet_by_index(0)
        for i in range(sheet.nrows):
            type=str(sheet.cell(i,2).value)
            slot=str(sheet.cell(i,1).value)
            sems=str(sheet.cell(i,0).value)
            courses=str(sheet.cell(i,3).value)
            if '.' in sems:
                sems=sems[:-2]
            print(type,slot,sems,courses)
            try:
                with transaction.atomic():
                    if '.' in sems:
                        sems=sems[:-2]
                    temppp(type, slot, sems, courses)
            except Exception as e:
                print(">>>>>>>",slot,e)
            

            
    else:
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)
