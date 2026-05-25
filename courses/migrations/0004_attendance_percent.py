from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_attendance'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='attendance_percent',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
