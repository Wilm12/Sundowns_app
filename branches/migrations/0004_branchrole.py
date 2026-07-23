from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('branches', '0003_branchpolicy'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('PRESIDENT', 'President'), ('SECRETARY', 'Secretary'), ('JOURNEY_COORDINATOR', 'Journey Coordinator'), ('TRANSPORT_COORDINATOR', 'Transport Coordinator'), ('TICKET_DISTRIBUTOR', 'Ticket Distributor'), ('STUDENT_VERIFIER', 'Student Verifier'), ('COMMUNICATIONS_OFFICER', 'Communications Officer')], max_length=30)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_branch_roles', to=settings.AUTH_USER_MODEL)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branch_roles', to='branches.branch')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branch_roles', to=settings.AUTH_USER_MODEL)),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name='branchrole',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('branch', 'user', 'role'), name='unique_active_branch_role_per_user_per_branch'),
        ),
    ]
