#!/usr/bin/env python
"""Test script to validate all PCMS imports and configurations."""
import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings.development'

import django
django.setup()

errors = []

# Test Models
try:
    from applications.placement_cell.models import (
        Company, JobPosting, JobApplication, InterviewSchedule,
        InterviewPanel, JobOffer, Announcement, PlacementPolicy, Constants
    )
    print("[OK] Models imported")
except Exception as e:
    errors.append("Models: " + str(e))
    print("[FAIL] Models: " + str(e))

# Test Forms
try:
    from applications.placement_cell.forms import (
        CompanyRegistrationForm, JobPostingForm, JobOfferForm,
        AnnouncementForm, InterviewScheduleForm, ReportFilterForm
    )
    print("[OK] Forms imported")
except Exception as e:
    errors.append("Forms: " + str(e))
    print("[FAIL] Forms: " + str(e))

# Test Utils
try:
    from applications.placement_cell.utils import (
        check_eligibility, check_duplicate_application,
        check_placement_policy, get_placement_statistics,
        get_student_application_summary, expire_pending_offers
    )
    print("[OK] Utils imported")
except Exception as e:
    errors.append("Utils: " + str(e))
    print("[FAIL] Utils: " + str(e))

# Test Views
try:
    from applications.placement_cell.views import (
        pcms_dashboard, company_list, register_company, approve_company,
        company_detail, job_posting_list, create_job_posting,
        job_posting_detail, edit_job_posting, toggle_job_posting,
        apply_for_job, my_applications, manage_applications, bulk_shortlist,
        schedule_interview, interview_detail, extend_offer, my_offers,
        respond_to_offer, all_offers, placement_reports,
        announcement_list, create_announcement, announcement_detail,
        delete_announcement, manage_policies
    )
    print("[OK] Views imported")
except Exception as e:
    errors.append("Views: " + str(e))
    print("[FAIL] Views: " + str(e))

# Test Admin
try:
    from applications.placement_cell.admin import (
        CompanyAdmin, JobPostingAdmin, JobApplicationAdmin,
        InterviewScheduleAdmin, JobOfferAdmin, AnnouncementAdmin,
        PlacementPolicyAdmin
    )
    print("[OK] Admin imported")
except Exception as e:
    errors.append("Admin: " + str(e))
    print("[FAIL] Admin: " + str(e))

# Test Serializers
try:
    from applications.placement_cell.api.serializers import (
        CompanySerializer, CompanyListSerializer,
        JobPostingSerializer, JobPostingListSerializer,
        JobApplicationSerializer, InterviewScheduleSerializer,
        InterviewPanelSerializer, JobOfferSerializer,
        AnnouncementSerializer, PlacementPolicySerializer
    )
    print("[OK] Serializers imported")
except Exception as e:
    errors.append("Serializers: " + str(e))
    print("[FAIL] Serializers: " + str(e))

# Test API Views
try:
    from applications.placement_cell.api.views import (
        CompanyViewSet, JobPostingViewSet, JobApplicationViewSet,
        JobOfferViewSet, AnnouncementViewSet,
        placement_stats_api, my_application_summary_api
    )
    print("[OK] API Views imported")
except Exception as e:
    errors.append("API Views: " + str(e))
    print("[FAIL] API Views: " + str(e))

# Test URL configuration
try:
    from applications.placement_cell.urls import urlpatterns
    pcms_urls = [p.name for p in urlpatterns if hasattr(p, 'name') and p.name]
    expected = ['pcms_dashboard', 'company_list', 'register_company',
                'job_posting_list', 'create_job_posting', 'my_applications',
                'my_offers', 'all_offers', 'placement_reports',
                'announcement_list', 'manage_policies']
    missing = [u for u in expected if u not in pcms_urls]
    if missing:
        errors.append("Missing URLs: " + str(missing))
        print("[FAIL] Missing URLs: " + str(missing))
    else:
        print("[OK] All URL patterns present (" + str(len(urlpatterns)) + " total)")
except Exception as e:
    errors.append("URLs: " + str(e))
    print("[FAIL] URLs: " + str(e))

# Test Constants
try:
    assert hasattr(Constants, 'COMPANY_APPROVAL_STATUS')
    assert hasattr(Constants, 'JOB_TYPE')
    assert hasattr(Constants, 'APPLICATION_STATUS')
    assert hasattr(Constants, 'INTERVIEW_MODE')
    assert hasattr(Constants, 'OFFER_STATUS')
    assert hasattr(Constants, 'ANNOUNCEMENT_TYPE')
    print("[OK] Constants verified")
except Exception as e:
    errors.append("Constants: " + str(e))
    print("[FAIL] Constants: " + str(e))

# Test Notification integration
try:
    from notification.views import placement_cell_notif
    print("[OK] Notification integration")
except Exception as e:
    errors.append("Notification: " + str(e))
    print("[FAIL] Notification: " + str(e))

print("\n" + "=" * 50)
if errors:
    print("FAILED with " + str(len(errors)) + " error(s):")
    for e in errors:
        print("  - " + e)
    sys.exit(1)
else:
    print("ALL CHECKS PASSED!")
    sys.exit(0)

