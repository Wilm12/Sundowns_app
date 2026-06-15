from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0004_alter_reward_options_alter_rewardredemption_options'),
    ]

    operations = [
        # No DB schema change required for TextChoices update; this migration
        # acts as a logical marker so migrations remain consistent across
        # environments when deployment updates introduce new statuses.
    ]
