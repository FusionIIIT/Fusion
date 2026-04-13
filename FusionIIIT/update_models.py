import re

filepath = 'applications/scholarships/models.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r"status = models\.CharField\(max_length=\d+, choices=\[\s+\('SUBMITTED', 'Submitted'\),\s+\('UNDER_REVIEW', 'Under Review'\),\s+\('APPROVED', 'Approved'\),\s+\('REJECTED', 'Rejected'\),\s+\], default='SUBMITTED'\)", 
    '''status = models.CharField(max_length=50, choices=[
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('FORWARDED_TO_CONVENOR', 'Forwarded to Convenor'),
        ('CORRECTION_REQUIRED', 'Correction Required'),
    ], default='SUBMITTED')''', text, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("Models updated via regex.")
