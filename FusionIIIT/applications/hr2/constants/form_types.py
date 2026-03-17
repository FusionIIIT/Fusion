from django.db import models


class FormType(models.TextChoices):
    LTC = "LTC", "LTC"
    CPDA_ADVANCE = "CPDAAdvance", "CPDA Advance"
    CPDA_REIMBURSEMENT = "CPDAReimbursement", "CPDA Reimbursement"
    LEAVE = "Leave", "Leave"
    APPRAISAL = "Appraisal", "Appraisal"
