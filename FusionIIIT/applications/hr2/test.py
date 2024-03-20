def ltc_pre_processing(request):
    ltc_form_data = {}

    # Extract general information
    ltc_form_data['name'] = request.POST['name']
    ltc_form_data['block_year'] = int(request.POST['block_year'])
    ltc_form_data['pf_no'] = int(request.POST['pf_no'])
    ltc_form_data['basic_pay_salary'] = int(request.POST['basic_pay_salary'])
    ltc_form_data['designation'] = request.POST['designation']
    ltc_form_data['department_info'] = request.POST['department_info']
    ltc_form_data['leave_availability'] = request.POST.getlist('leave_availability') == ['True', 'True']
    ltc_form_data['leave_start_date'] = request.POST['leave_start_date']
    ltc_form_data['leave_end_date'] = request.POST['leave_end_date']
    ltc_form_data['date_of_leave_for_family'] = request.POST['date_of_leave_for_family']
    ltc_form_data['nature_of_leave'] = request.POST['nature_of_leave']
    ltc_form_data['purpose_of_leave'] = request.POST['purpose_of_leave']
    ltc_form_data['hometown_or_not'] = request.POST.get('hometown_or_not') == 'True'
    ltc_form_data['place_of_visit'] = request.POST['place_of_visit']
    ltc_form_data['address_during_leave'] = request.POST['address_during_leave']

    # Extract details of family members
    family_members = []
    for i in range(1, 7):
        if request.POST.get(f'info_{i}_1'):
            family_member = ','.join(request.POST.getlist(f'info_{i}_{j}')[0] for j in range(1, 4))
            family_members.append(family_member)
    ltc_form_data['details_of_family_members_already_done'] = ','.join(family_members)

    # Extract details of dependents
    dependents = []
    for i in range(1, 7):
        if request.POST.get(f'd_info_{i}_1'):
            dependent = ','.join(request.POST.getlist(f'd_info_{i}_{j}')[0] for j in range(1, 5))
            dependents.append(dependent)
    ltc_form_data['details_of_dependents'] = ','.join(dependents)

    # Extract remaining fields
    ltc_form_data['amount_of_advance_required'] = int(request.POST['amount_of_advance_required'])
    ltc_form_data['certified_family_dependents'] = request.POST['certified_family_dependents']
    ltc_form_data['certified_advance'] = int(request.POST['certified_advance'])
    ltc_form_data['adjusted_month'] = request.POST['adjusted_month']
    ltc_form_data['date'] = request.POST['date']
    ltc_form_data['phone_number_for_contact'] = int(request.POST['phone_number_for_contact'])

    return ltc_form_data

# Example usage
request_data = {
    'csrfmiddlewaretoken': ['yLyPMZMWRBnDU3hSh5kPGq6AgOFNY5WTK1HaZxAuiozCzXBf8qfOML5irZJd8MkM'],
    'block_year': ['232'],
    'pf_no': ['222'],
    'basic_pay_salary': ['2322'],
    'name': ['dsds'],
    'designation': ['dsdsd'],
    'department_info': ['ds'],
    'leave_availability': ['True', 'True'],
    'leave_start_date': ['2024-02-22'],
    'leave_end_date': ['2024-02-22'],
    'date_of_leave_for_family': ['2024-02-22'],
    'nature_of_leave': ['dsds'],
    'purpose_of_leave': ['dsdsd'],
    'hometown_or_not': ['True'],
    'place_of_visit': [''],
    'address_during_leave': ['full street address'],
    'details_of_family_members_already_done': ['sds', 'dsd', 'dsd'],
    'info_1_1': ['1'],
    'info_1_2': ['dsds'],
    'info_1_3': ['12'],
    'info_2_1': ['2'],
    'info_2_2': ['sds'],
    'info_2_3': ['121'],
    'info_3_1': ['3'],
    'info_3_2': ['dsds'],
    'info_3_3': ['21'],
    'info_4_1': [''],
    'info_4_2': [''],
    'info_4_3': [''],
    'info_5_1': [''],
    'info_5_2': [''],
    'info_5_3': [''],
    'info_6_1': [''],
    'info_6_2': [''],
    'info_6_3': [''],
    'd_info_1_1': ['1'],
    'd_info_1_2': ['sds'],
    'd_info_1_3': ['21'],
    'd_info_1_4': ['sdd'],
    'd_info_2_1': ['2'],
    'd_info_2_2': ['dsd'],
    'd_info_2_3': ['23'],
    'd_info_2_4': ['sds'],
    'd_info_3_1': ['3'],
    'd_info_3_2': ['sd'],
    'd_info_3_3': ['21'],
    'd_info_3_4': ['dds'],
    'd_info_4_1': [''],
    'd_info_4_2': [''],
    'd_info_4_3': [''],
    'd_info_4_4': [''],
    'd_info_5_1': [''],
    'd_info_5_2': [''],
    'd_info_5_3': [''],
    'd_info_5_4': [''],
    'd_info_6_1': [''],
    'd_info_6_2': [''],
    'd_info_6_3': [''],
    'd_info_6_4': [''],
    'amount_of_advance_required': ['211'],
    'certified_family_dependents': ['dqwd'],
    'certified_advance': ['dqwd'],
    'adjusted_month': ['qwdwd'],
    'date': ['2024-02-22'],
    'phone_number_for_contact': ['2312123']
}

print(ltc_pre_processing(request_data))
