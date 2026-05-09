from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0005_moduleaccess_database'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetOTP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(db_index=True, max_length=150)),
                ('otp_hash', models.CharField(max_length=64)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('send_count', models.PositiveSmallIntegerField(default=1)),
                ('window_start', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('reset_token_hash', models.CharField(blank=True, max_length=64, null=True)),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('token_used', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddConstraint(
            model_name='passwordresetotp',
            constraint=models.UniqueConstraint(fields=('username',), name='unique_active_otp_per_user'),
        ),
    ]
