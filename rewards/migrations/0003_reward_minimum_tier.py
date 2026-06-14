# Generated migration to add minimum_tier to Reward
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0002_reward_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='reward',
            name='minimum_tier',
            field=models.CharField(choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], default='bronze', max_length=10),
        ),
    ]
