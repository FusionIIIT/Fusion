from django.db import models

# Create your models here.

class Job(models.Model):
    id                  = models.AutoField(primary_key=True)
    start_date          = models.DateField()
    end_date            = models.DateField()
    skill_required      = models.TextField(max_length=500)
    job_title           = models.CharField(max_length=300)
    job_description     = models.TextField()
    job_recommendedby   = models.ForeignKey(Alumni,on_delete=models.CASCADE)
    job_company         = models.TextField()
    job_link            = models.URLField()

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Job'

class Alumni(models.Model):
    alumni_roll         = models.IntegerField(primary_key=True, null=False, blank=false)
    alumni_name         = models.TextField()
    alumni_linkedinurl  = models.URLField()
    alumni_batch        = models.IntegerField()
    alumni_experience   = models.TextField()
    alumni_role         = models.TextField()
    alumni_company      = models.TextField()

    def __str__(self):
        return str(self.alumni_roll)

    class Meta:
        db_table = 'Alumni'

