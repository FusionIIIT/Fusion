from django.db import models

# Create your models here.

class Job(models.Model):
    start_date = models.DateField()
    end_date=models.DateField()
    skill_required=models.TextField(max_length=500)
    job_title = models.CharField(max_length=300)
    job_description = models.TextField()
    job_recommendedby = models.ForeignKey(Alumni,on_delete=models.CASCADE)
    job_company = models.TextField()

    class Meta:
        db_table = 'Job'

class Alumni(models.Model):
    alumni_roll = models.IntegerField(primary_key=True, null=False)
    alumni_name = models.TextField()
    alumni_linkedinurl = models.URLField()
    alumni_batch = models.IntegerField()

    def __str__(self):
        return str(self.alumni_roll)

    class Meta:
        db_table = 'Alumni'

