"""
Awards API — URL Config
awardsScholarships/api/urls_awards.py
"""
from django.conf.urls import url
from .views_awards import (
    AwardsStudentProfileView,
    GenerateAutoAwardsView,
    AutoAwardsListView,
    AutoAwardsExportView,
    AwardApplicationView,
    AwardApplicationListView,
    AwardApplicationExportView,
    StudentAwardApplicationsView,
    AwardSettingsView,
)

urlpatterns = [
    # ── Config ────────────────────────────────────────────────────────────────
    url(r'^settings/$',              AwardSettingsView.as_view(),          name='awards-settings'),

    # ── Student ──────────────────────────────────────────────────────────────
    url(r'^student-profile/$',       AwardsStudentProfileView.as_view(),   name='awards-student-profile'),
    url(r'^student-applications/$',  StudentAwardApplicationsView.as_view(),name='awards-my-applications'),
    url(r'^auto-awards/$',           AutoAwardsListView.as_view(),         name='awards-auto-list'),
    url(r'^apply/$',                 AwardApplicationView.as_view(),       name='awards-apply'),

    # ── Assistant ─────────────────────────────────────────────────────────────
    url(r'^generate-auto-awards/$',  GenerateAutoAwardsView.as_view(),     name='awards-generate'),
    url(r'^applications/$',          AwardApplicationListView.as_view(),   name='awards-applications'),
    url(r'^applications/export/$',   AwardApplicationExportView.as_view(), name='awards-app-export'),
    url(r'^auto-awards/export/$',    AutoAwardsExportView.as_view(),       name='awards-auto-export'),
]
