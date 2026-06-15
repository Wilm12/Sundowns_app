from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0005_rewardredemption_statuses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rewardredemption',
            name='status',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('pending', 'Pending'),
                    ('approved', 'Approved'),
                    ('ready_for_collection', 'Ready for Collection'),
                    ('collected', 'Collected'),
                    ('completed', 'Completed'),
                    ('rejected', 'Rejected'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
            ),
        ),
    ]
