Mcm_list = [
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

Mcm_schema = {
    "brother_name": {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]},
    "brother_occupation": {
        "anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]
    },
    "sister_name": {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]},
    "sister_occupation": {
        "anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]
    },
    "income_father": {"type": "number"},
    "income_mother": {"type": "number"},
    "income_other": {"type": "number"},
    "father_occ": {"type": "string", "maxLength": 10},
    "mother_occ": {"type": "string", "maxLength": 10},
    "father_occ_desc": {
        "anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]
    },
    "mother_occ_desc": {
        "anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]
    },
    "four_wheeler": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "four_wheeler_desc": {
        "anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]
    },
    "two_wheeler": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "two_wheeler_desc": {
        "anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]
    },
    "house": {"anuOf": [{"type": "string", "maxLength": 10}, {"type": "null"}]},
    "plot_area": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "constructed_area": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "school_fee": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "school_name": {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]},
    "bank_name": {"anuOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]},
    "loan_amount": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "college_fee": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "college_name": {"anuOf": [{"type": "string", "maxLength": 30}, {"type": "null"}]},
    "status": {"anuOf": [{"type": "string", "maxLength": 10}, {"type": "null"}]},
    "annual_income": {"anuOf": [{"type": "number"}, {"type": "null"}]},
}

Director_gold_list = [
    "award_id",
    "financial_assistance",
    "academic",
    "science",
    "games",
    "cultural",
    "social",
    "corporate",
    "hall_activities",
    "gymkhana_activities",
    "institute_activities",
    "counselling_activities",
    "other_extra_curricular_activities",
    "sci",
    "scie",
    "ij",
    "ic",
    "nc",
    "workshop",
    "novelty",
    "disciplinary_action",
]

Director_gold_schema = {
    "award_id": {"anuof": [{"type": "string", "maxLength": 100}, {"type": ""}]},
    "financial_assistance": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "academic": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "science": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "games": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "cultural": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "social": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "corporate": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "hall_activities": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "gymkhana_activities": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "institute_activities": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "counselling_activities": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "other_extra_curricular_activities": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sci": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "scie": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ij": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ic": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "nc": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "workshop": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "novelty": {"anuof": [{"type": "string", "maxLength": 200}, {"type": "null"}]},
    "disciplinary_action": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
}

Director_silver_list = [
    "award_id",
    "cultural_intercollege_certificates_no",
    "cultural_intercollege_team_event",
    "cultural_intercollege_team_certificates_no",
    "culturalfest_certificates_no",
    "cultural_club_coordinator",
    "cultural_club_co_coordinator",
    "cultural_event_member",
    "cultural_interIIIT_certificates_no",
    "cultural_interIIIT_team_certificates_no",
    "sports_club_coordinator",
    "sports_club_co_coordinator",
    "sports_event_member",
    "sports_other_accomplishment",
]

Director_silver_schema = {
    "award_id": {"anuof": [{"type": "string", "maxLength": 100}, {"type": ""}]},
    "cultural_intercollege_certificates_no": {
        "anuOf": [{"type": "number"}, {"type": "null"}]
    },
    "cultural_intercollege_team_event": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "cultural_intercollege_team_certificates_no": {
        "anuOf": [{"type": "number"}, {"type": "null"}]
    },
    "culturalfest_certificates_no": {"anuOf": [{"type": "number"}, {"type": "null"}]},
    "cultural_club_coordinator": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "cultural_club_co_coordinator": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "cultural_event_member": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "cultural_interIIIT_certificates_no": {
        "anuOf": [{"type": "number"}, {"type": "null"}]
    },
    "cultural_interIIIT_team_certificates_no": {
        "anuOf": [{"type": "number"}, {"type": "null"}]
    },
    "sports_club_coordinator": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sports_club_co_coordinator": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sports_event_member": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sports_other_accomplishment": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
}

DM_Proficiency_Gold_list = [
    "award_id",
    "brief_description_project",
    "project_grade",
    "cross_disciplinary",
    "project_publication",
    "project_type",
    "patent_ipr_project",
    "prototype_available",
    "team_members_name",
    "team_members_cpi",
    "project_evaluation_prototype",
    "project_utility",
    "sports_cultural",
    "sci",
    "esci",
    "scie",
    "ij",
    "ic",
    "nc",
    "workshop",
]

DM_Proficiency_Gold_schema = {
    "award_id": {"anuof": [{"type": "string", "maxLength": 100}, {"type": ""}]},
    "brief_description_project": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_grade": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "cross_disciplinary": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_publication": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_type": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "patent_ipr_project": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "prototype_available": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "team_members_name": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "team_members_cpi": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_evaluation_prototype": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_utility": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sports_cultural": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sci": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "esci": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "scie": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ij": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ic": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "nc": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "workshop": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
}

IIITDM_Proficiency_list = [
    "project_objectives",
    "project_mentor",
    "project_outcome",
    "research_Or_Patent_Detail",
    "project_Beneficial",
    "improvement_Done",
    "sci",
    "esci",
    "scie",
    "ij",
    "ic",
    "nc",
    "indian_national_Conference",
    "international_Conference",
    "patent_Status",
    "interdisciplinary_Criteria",
    "awards_Recieved_Workshop",
    "placement_Status",
    "workshop",
    "prototype",
    "utility",
    "core_Area",
    "technology_Transfer",
]

IIITDM_Proficiency_schema = {
    "project_objectives": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_mentor": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_outcome": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "research_Or_Patent_Detail": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "project_Beneficial": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "improvement_Done": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "sci": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "esci": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "scie": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ij": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "ic": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "nc": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "indian_national_Conference": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "international_Conference": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "patent_Status": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "interdisciplinary_Criteria": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "awards_Recieved_Workshop": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "placement_Status": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
    "workshop": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "prototype": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "utility": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "core_Area": {"anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]},
    "technology_Transfer": {
        "anuof": [{"type": "string", "maxLength": 1000}, {"type": "null"}]
    },
}
