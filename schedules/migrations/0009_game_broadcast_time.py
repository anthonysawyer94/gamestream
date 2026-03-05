from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0008_game_leaderboard'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='broadcast_time',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
