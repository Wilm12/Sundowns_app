from django.db import migrations, models
import django.db.models.deletion


def create_default_policies(apps, schema_editor):
    Branch = apps.get_model('branches', 'Branch')
    BranchPolicy = apps.get_model('branches', 'BranchPolicy')
    for branch in Branch.objects.all():
        BranchPolicy.objects.get_or_create(branch=branch)


class Migration(migrations.Migration):
    dependencies = [
        ('branches', '0002_branch_branch_code_branch_contact_email_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_verification_required', models.BooleanField(default=True)),
                ('booking_deadline_hours', models.PositiveIntegerField(default=24)),
                ('maximum_bus_capacity', models.PositiveIntegerField(default=100)),
                ('attendance_threshold', models.PositiveIntegerField(default=70)),
                ('allow_guest_supporters', models.BooleanField(default=False)),
                ('announcement_requires_approval', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='branch_policy', to='branches.branch')),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name='branchpolicy',
            constraint=models.UniqueConstraint(fields=('branch',), name='unique_branch_policy_per_branch'),
        ),
        migrations.RunPython(create_default_policies, migrations.RunPython.noop),
    ]
