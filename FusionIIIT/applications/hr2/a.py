def reverse_ltc_pre_processing(data):
    reversed_data = {}

    # Copying over simple key-value pairs
    simple_keys = [
        'block_year', 'pf_no', 'basic_pay_salary', 'name', 'designation', 'department_info',
        'leave_availability', 'leave_start_date', 'leave_end_date', 'date_of_leave_for_family',
        'nature_of_leave', 'purpose_of_leave', 'hometown_or_not', 'place_of_visit',
        'address_during_leave', 'amount_of_advance_required', 'certified_family_dependents',
        'certified_advance', 'adjusted_month', 'date', 'phone_number_for_contact'
    ]
    for key in simple_keys:
        value = data[key]
        reversed_data[key] = value if value != 'None' else ''

    # Reversing array-like values
    reversed_data['details_of_family_members_already_done'] = data['details_of_family_members_already_done'].split(',')
    
    family_members_about_to_avail = data['family_members_about_to_avail'].split(',')
    for index, value in enumerate(family_members_about_to_avail):
        family_members_about_to_avail[index] = value if value != 'None' else ''
    
    reversed_data['info_1_1'] = family_members_about_to_avail[0]
    reversed_data['info_1_2'] = family_members_about_to_avail[1]
    reversed_data['info_1_3'] = family_members_about_to_avail[2]
    reversed_data['info_2_1'] = family_members_about_to_avail[3]
    reversed_data['info_2_2'] = family_members_about_to_avail[4]
    reversed_data['info_2_3'] = family_members_about_to_avail[5]
    reversed_data['info_3_1'] = family_members_about_to_avail[6]
    reversed_data['info_3_2'] = family_members_about_to_avail[7]
    reversed_data['info_3_3'] = family_members_about_to_avail[8]

    # Reversing details_of_dependents
    details_of_dependents = data['details_of_dependents'].split(',')
    for i in range(1, 7):
        for j in range(1, 4):
            key = f'd_info_{i}_{j}'
            value = details_of_dependents.pop(0)
            reversed_data[key] = value if value != 'None' else ''

    return reversed_data

# Sample data
data = {
    'block_year': '232', 'pf_no': '4324', 'basic_pay_salary': '324', 'name': 'sdf', 'designation': 'fds',
    'department_info': 'dfs', 'leave_availability': 'True', 'leave_start_date': '2024-03-13',
    'leave_end_date': '2024-03-17', 'date_of_leave_for_family': '2024-03-16', 'nature_of_leave': 'erds',
    'purpose_of_leave': 'fds', 'hometown_or_not': 'True', 'place_of_visit': 'fds', 'address_during_leave': 'dfsfsdf',
    'details_of_family_members_already_done': 'fds,dfs,dfs', 'family_members_about_to_avail': '1,dfsf,21,2,dsf,23,3,dfs,12',
    'details_of_dependents': '1,ds,12,2,sds,2,3,ds,13,None,None,None,None,None,None,None,None,None', 'amount_of_advance_required': '1221',
    'certified_family_dependents': '213', 'certified_advance': '213', 'adjusted_month': '213', 'date': '2024-03-15',
    'phone_number_for_contact': '21313123132'
}

# Reverse processing
reversed_data = reverse_ltc_pre_processing(data)
print(reversed_data)



{'block_year': 232, 'pf_no': None, 'basic_pay_salary': 324, 'name': 'sdf', 'designation': 'fds',
  'department_info': 'dfs', 'leave_availability': True, 'leave_start_date': datetime.date(2024, 3, 13),
    'leave_end_date': datetime.date(2024, 3, 17), 'date_of_leave_for_family': datetime.date(2024, 3, 16), 
    'nature_of_leave': 'erds', 'purpose_of_leave': 'fds', 'hometown_or_not': True, 'place_of_visit': 'fds',
      'address_during_leave': 'dfsfsdf', 'amount_of_advance_required': 1221, 'certified_family_dependents': '213',
        'certified_advance': 213, 'adjusted_month': '213', 'date': datetime.date(2024, 3, 15), 
        'phone_number_for_contact': 21313123132, 
        'details_of_family_members_already_done': ['fds', 'dfs', 'dfs'], 
        'info_1_1': '1', 'info_1_2': 'dfsf', 'info_1_3': '21', 'info_2_1': 
        '2', 'info_2_2': 'dsf', 'info_2_3': '23', 'info_3_1': '3', 'info_3_2': 
        'dfs', 'info_3_3': '12', 'd_info_1_1': '1', 'd_info_1_2': 'ds', 'd_info_1_3': 
        '12', 'd_info_2_1': '2', 'd_info_2_2': 'sds', 'd_info_2_3': '2', 'd_info_3_1': '3',
          'd_info_3_2': 'ds', 'd_info_3_3': '13', 'd_info_4_1': '', 'd_info_4_2': '', 'd_info_4_3': '',
           
            'd_info_5_1': '', 'd_info_5_2': '', 'd_info_5_3': '', 'd_info_6_1': '', 'd_info_6_2': '', 'd_info_6_3': ''}
