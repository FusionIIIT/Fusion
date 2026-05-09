from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def dedupe_reports(apps, schema_editor):
    Report = apps.get_model('feeds', 'report')
    seen = set()
    duplicate_ids = []

    for report in Report.objects.order_by('id').iterator():
        key = (report.user_id, report.question_id)
        if key in seen:
            duplicate_ids.append(report.id)
        else:
            seen.add(key)

    if duplicate_ids:
        Report.objects.filter(id__in=duplicate_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answeraquestion',
            name='answers',
            field=models.ManyToManyField(blank=True, related_name='answers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='answeraquestion',
            name='dislikes',
            field=models.ManyToManyField(blank=True, related_name='answer_dislikes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='answeraquestion',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='answer_likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='answeraquestion',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.askaquestion'),
        ),
        migrations.AlterField(
            model_name='answeraquestion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='askaquestion',
            name='dislikes',
            field=models.ManyToManyField(blank=True, related_name='dislikes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='askaquestion',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='askaquestion',
            name='requests',
            field=models.ManyToManyField(blank=True, related_name='requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='askaquestion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comments',
            name='likes_comment',
            field=models.ManyToManyField(blank=True, related_name='likes_comment', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comments',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.askaquestion'),
        ),
        migrations.AlterField(
            model_name='comments',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='hidden',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.askaquestion'),
        ),
        migrations.AlterField(
            model_name='hidden',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='questionaccesscontrol',
            name='posted_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.roles'),
        ),
        migrations.AlterField(
            model_name='questionaccesscontrol',
            name='question',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='question_list',
                to='feeds.askaquestion',
            ),
        ),
        migrations.AlterField(
            model_name='reply',
            name='comment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.comments'),
        ),
        migrations.AlterField(
            model_name='reply',
            name='replies',
            field=models.ManyToManyField(blank=True, related_name='replies', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reply',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='roles',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='report',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.askaquestion'),
        ),
        migrations.AlterField(
            model_name='report',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tags',
            name='my_subtag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feeds.alltags'),
        ),
        migrations.AlterField(
            model_name='tags',
            name='my_tag',
            field=models.CharField(
                choices=[
                    ('CSE', 'CSE'),
                    ('ECE', 'ECE'),
                    ('Mechanical', 'Mechanical'),
                    ('Technical-Clubs', 'Technical Clubs'),
                    ('Cultural-Clubs', 'Cultural Clubs'),
                    ('Sports-Clubs', 'Sports Clubs'),
                    ('Business-and-Career', 'Business and Career'),
                    ('Entertainment', 'Entertainment'),
                    ('IIITDMJ-Campus', 'IIITDMJ Campus'),
                    ('Jabalpur-city', 'Jabalpur city'),
                    ('IIITDMJ-Rules-and-Regulations', 'IIITDMJ rules and regulations'),
                    ('Academics', 'Academics'),
                    ('IIITDMJ', 'IIITDMJ'),
                    ('Life-Relationship-and-Self', 'Life Relationship and Self'),
                    ('Technology-and-Education', 'Technology and Education'),
                    ('Programmes', 'Programmes'),
                    ('Others', 'Others'),
                    ('Design', 'Design'),
                ],
                default='CSE',
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='tags',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(dedupe_reports, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together={('user', 'question')},
        ),
    ]
