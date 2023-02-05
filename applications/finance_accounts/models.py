from django.db import models


class Paymentscheme(models.Model):
    month = models.CharField(max_length = 70 , null = True)
    year = models.IntegerField(null = True)
    pf = models.IntegerField(null = True)
    name = models.CharField(max_length = 70)
    designation = models.CharField(max_length = 50)
    pay = models.IntegerField()
    gr_pay = models.IntegerField()
    da = models.IntegerField()
    ta = models.IntegerField()
    hra = models.IntegerField()
    fpa = models.IntegerField()
    special_allow = models.IntegerField()
    nps = models.IntegerField()
    gpf = models.IntegerField()
    income_tax = models.IntegerField()
    p_tax = models.IntegerField()
    gslis = models.IntegerField()
    gis = models.IntegerField()
    license_fee = models.IntegerField()
    electricity_charges = models.IntegerField()
    others = models.IntegerField()
    gr_reduction = models.IntegerField(default=0)
    net_payment = models.IntegerField(default=0)
    senior_verify = models.BooleanField(default = False)
    ass_registrar_verify = models.BooleanField(default = False)
    ass_registrar_aud_verify = models.BooleanField(default = False)
    registrar_director_verify = models.BooleanField(default = False)
    runpayroll = models.BooleanField(default = False)
    view = models.BooleanField(default = True)

    class Meta:
       constraints = [
            models.UniqueConstraint(fields=['month', 'year', 'pf'], name='Unique Contraint 1')
        ]


class Receipts(models.Model):
        receipt_id = models.AutoField(primary_key=True)
        TransactionId = models.IntegerField(default=0, unique=True)
        ToWhom = models.CharField(max_length=80)
        FromWhom = models.CharField(max_length=80)
        Purpose = models.CharField(max_length=20)
        Date = models.DateField()

class Payments(models.Model):
        payment_id = models.AutoField(primary_key=True)
        TransactionId = models.IntegerField(default=0, unique=True)
        ToWhom = models.CharField(max_length=80)
        FromWhom = models.CharField(max_length=80)
        Purpose = models.CharField(max_length=20)
        Date = models.DateField()

class Bank(models.Model):
        bank_id = models.AutoField(primary_key=True)
        Account_no = models.IntegerField(default=0, unique=True)
        Bank_Name = models.CharField(max_length=50)
        IFSC_Code = models.CharField(max_length=20, unique=True)
        Branch_Name = models.CharField(max_length=80)

        class Meta:
           constraints = [
                models.UniqueConstraint(fields=['Bank_Name','Branch_Name'], name='Unique Contraint 2')
            ]

class Company(models.Model):
        company_id = models.AutoField(primary_key=True)
        Company_Name = models.CharField(max_length=20, unique=True)
        Start_Date = models.DateField()
        End_Date = models.DateField(null = True, blank = True)
        Description = models.CharField(max_length=200)
        Status = models.CharField(max_length=200)
