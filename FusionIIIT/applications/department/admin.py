from django.contrib import admin

# Register your models here.
from .models import(Announcements, SpecialRequest)

admin.site.register(Announcements)
admin.site.register(SpecialRequest)

class admin(admin.Announcements):
    
    department = admin.CharField(max_length=100)
    date = admin.Charfield(max_length=100)
    name = admin.Charfield(max_length=100)
    
   # Once you've defined your model, you can create the 
    #corresponding database table by running migrations. 
    #In the terminal, navigate to your project directory 
    #and run the following commands:
    
    #python manage.py makemigrations 
    #python manage.py migrate
    
    admin = admin (department='CSE',date='10-02-2022',name='wwwww')
    admin.save()
    
    admin = admin(department='ECE',date='10-02-2022',name='wxwwww')
    admin.save()
    
    admin = admin(department='MECH',date='10-02-2022',name='wxxwwww')
    admin.save()
    
    admin = admin(department='DESIGN',date='10-02-2022',name='wxxxwwww')
    admin.save()
