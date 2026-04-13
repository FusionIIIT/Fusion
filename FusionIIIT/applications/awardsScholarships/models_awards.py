"""
Awards Module — Django Models
awardsScholarships/models_awards.py

New models for the Awards module (kept separate from existing models.py
to avoid touching legacy scholarship code).

Registered in apps.py via proxy — imported from here.
"""
import datetime
from django.db import models
from applications.globals.models import ExtraInfo
from applications.academic_information.models import Student


# ─── Grade point mapping ──────────────────────────────────────────────────────
GRADE_POINTS = {
    'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6,
    'C+': 5, 'C': 4, 'D+': 3, 'D': 2, 'F': 0,
    # legacy variants
    '10': 10, '9': 9, '8': 8, '7': 7, '6': 6,
    '5': 5, '4': 4, '3': 3, '2': 2, '0': 0,
}

# ─── Auto Award Results ────────────────────────────────────────────────────────

class AutoAwardResult(models.Model):
    """
    Stores the output of the automatic award generation algorithm.
    One row per (award_name, student) per generation run. Old runs are
    cleared before a new one is saved (replace strategy).
    """
    AWARD_CHOICES = [
        ('CGM', "Chairman's Gold Medal"),
        ('DGM_UG', "Director's Gold Medal (UG)"),
        ('DGM_PG', "Director's Gold Medal (PG)"),
        ('ASM_BTECH_CSE', 'Academic Silver Medal — B.Tech CSE'),
        ('ASM_BTECH_ECE', 'Academic Silver Medal — B.Tech ECE'),
        ('ASM_BTECH_ME',  'Academic Silver Medal — B.Tech ME'),
        ('ASM_BTECH_SM',  'Academic Silver Medal — B.Tech SM'),
        ('ASM_BDES',      'Academic Silver Medal — B.Des'),
        ('ASM_MTECH_CSE', 'Academic Silver Medal — M.Tech CSE'),
        ('ASM_MTECH_ECE', 'Academic Silver Medal — M.Tech ECE'),
        ('ASM_PHD',       'Academic Silver Medal — PhD'),
    ]

    award_name   = models.CharField(max_length=100)
    award_code   = models.CharField(max_length=30, choices=AWARD_CHOICES, default='CGM')
    student      = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='auto_awards')
    cpi          = models.FloatField(default=0.0)
    programme    = models.CharField(max_length=20, blank=True)
    branch       = models.CharField(max_length=50, blank=True)
    batch        = models.IntegerField(default=2023)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'applications.awardsScholarships'
        db_table = 'awards_auto_award_result'

    def __str__(self):
        return f"{self.award_name} — {self.student}"


# ─── Application-Based Award Applications ────────────────────────────────────

class AwardApplication(models.Model):
    """
    Stores student applications for activity-based awards.
    form_data is stored as JSON for flexibility across award types.
    """
    AWARD_TYPE_CHOICES = [
        ('IIITDM_PRIZE',  'IIITDM Proficiency Prize'),
        ('CULTURAL',      'Cultural Medal'),
        ('SPORTS',        'Sports Medal'),
        ('DM_PROFICIENCY','D&M Proficiency Gold Medal'),
        ('DIRECTOR_SILVER','Director Silver Medal'),
    ]

    student     = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='award_applications')
    award_type  = models.CharField(max_length=30, choices=AWARD_TYPE_CHOICES)
    form_data   = models.JSONField(default=dict)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'applications.awardsScholarships'
        db_table = 'awards_award_application'
        # One application per award type per student
        unique_together = ('student', 'award_type')

    def __str__(self):
        return f"{self.student} — {self.get_award_type_display()}"
