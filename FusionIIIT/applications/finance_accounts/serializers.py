from rest_framework import serializers
from applications.finance_accounts.models import *


class PaymentschemeSerializer(serializers.ModelSerializer):

    class Meta:
        model=Paymentscheme
        fields=('__all__')

class ReceiptsSerializer(serializers.ModelSerializer):

    class Meta:
        model=Receipts
        fields=('__all__')

class PaymentsSerializer(serializers.ModelSerializer):

    class Meta:
        model=Payments
        fields=('__all__')        

class BankSerializer(serializers.ModelSerializer):

    class Meta:
        model=Bank
        fields=('__all__') 

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model=Company
        fields=('__all__')                 