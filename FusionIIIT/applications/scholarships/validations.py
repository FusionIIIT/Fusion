# validation for MCM form

brother_name = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
brother_occupation = {"anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}
sister_name = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
sister_occupation = {"anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}
income_father = {"type": "number"}
income_mother = {"type": "number"}
income_other = {"type": "number"}
father_occ = {"type": "string", "maxLength": 10}
mother_occ = {"type": "string", "maxLength": 10}
father_occ_desc = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
mother_occ_desc = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
four_wheeler = {"anuOf": [{"type": "number"}, {"type": "null"}]}
four_wheeler_desc = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
two_wheeler = {"anuOf": [{"type": "number"}, {"type": "null"}]}
two_wheeler_desc = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
house = {"anuOf": [{"type": "string", "maxLength": 10}, {"type": "null"}]}
plot_area = {"anuOf": [{"type": "number"}, {"type": "null"}]}
constructed_area = {"anuOf": [{"type": "number"}, {"type": "null"}]}
school_fee = {"anuOf": [{"type": "number"}, {"type": "null"}]}
school_name = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
bank_name = {"anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}
loan_amount = {"anuOf": [{"type": "number"}, {"type": "null"}]}
college_fee = {"anuOf": [{"type": "number"}, {"type": "null"}]}
college_name = {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]}
status = {"anuOf": [{"type": "string", "maxLength": 10}, {"type": "null"}]}
annual_income = {"anuOf": [{"type": "number"}, {"type": "null"}]}
# income_certificate
# forms
# student
# date
# award_id

MCM_list = [
    "brother_name",
    "brother_occupation",
    "sister_name",
    "sister_occupation",
    "income_father",
    "income_mother",
    "income_other",
    "father_occ",
    "mother_occ",
    "father_occ_desc",
    "mother_occ_desc",
    "four_wheeler",
    "four_wheeler_desc",
    "two_wheeler",
    "two_wheeler_desc",
    "house",
    "plot_area",
    "constructed_area",
    "school_fee",
    "school_name",
    "bank_name",
    "loan_amount",
    "college_fee",
    "college_name",
    "annual_income",
]
