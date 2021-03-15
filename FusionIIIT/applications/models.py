from django.db import models

# Create your models here. The User and the admins table is just for the our authentication purpose and in fusion,
# authentication would be handled by integration team. We have made it for test purpose and for presentation purpose
# at time of evaluation Also, some tables are new in themselves while others are just using columns in original
# tables to fill their columns.
#
class requestModel(models.Model):
    id = models.ForeignKey()
    type = models.CharField()
    description = models.CharField(max_length=50)

class notification(models.Model):
    id=models.ForeignKey()
    description=models.CharField()

class requestModel(models.Model):
    id = models.ForeignKey()
    type = models.CharField()
    description = models.CharField(max_length=50)

class Users(models.Model):
    id = models.ForeignKey(Student, to_field='id',primary_key=True)
    Address = models.CharField(max_length=50)
    password = models.CharField()
# Tables till now will have id column as foreign key to reference global id database(just shown by FK,
# not implemented fully)

class projectsstatus(models.Model):
    description=models.CharField()
    status = models.CharField()


class Admins(models.Model):
    id = models.CharField()
    password = models.CharField()