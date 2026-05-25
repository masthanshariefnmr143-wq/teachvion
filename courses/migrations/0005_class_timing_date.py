from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_attendance_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='classtiming',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='classtiming',
            name='day_of_week',
            field=models.CharField(blank=True, choices=[('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday')], max_length=3),
        ),
    ]
