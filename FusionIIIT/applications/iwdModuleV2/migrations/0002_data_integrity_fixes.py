from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iwdModuleV2', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addendum',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='agreement',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='corrigendumtable',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='financialbiddetails',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='letterofintentdetails',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='nooftechnicalbidtimes',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='prebiddetails',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='technicalbiddetails',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
        migrations.AlterField(
            model_name='workorderform',
            name='key',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='iwdModuleV2.projects'),
        ),
    ]
