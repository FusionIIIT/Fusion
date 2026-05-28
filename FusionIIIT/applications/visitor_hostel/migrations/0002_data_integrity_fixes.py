from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('visitor_hostel', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='meal_bill',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='bill',
            name='room_bill',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='bookingdetail',
            name='caretaker',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='caretaker',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='bookingdetail',
            name='number_of_rooms',
            field=models.IntegerField(
                blank=True,
                default=1,
                null=True,
                validators=[MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name='bookingdetail',
            name='number_of_rooms_alloted',
            field=models.IntegerField(
                blank=True,
                default=1,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AlterField(
            model_name='bookingdetail',
            name='person_count',
            field=models.IntegerField(default=1, validators=[MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='addition_stock',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='inuse',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='non_serviceable',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='opening_stock',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='quantity',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='serviceable',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='total_stock',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='total_usable',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='inventorybill',
            name='cost',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='mealrecord',
            name='persons',
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='mealrecord',
            name='room',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='visitor_hostel.roomdetail',
            ),
        ),
    ]
