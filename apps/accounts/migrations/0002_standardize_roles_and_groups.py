# Generated manually for RBAC Role Standardization and Group Sync
from django.db import migrations, models


def initialize_groups_and_standardize_roles(apps, schema_editor):
    UserAccount = apps.get_model('accounts', 'UserAccount')
    Group = apps.get_model('auth', 'Group')

    # 1. Create standard institutional groups
    primary_roles = ['ADMIN', 'FACULTY', 'OFFICE_STAFF', 'STUDENT']
    group_map = {}
    for role_name in primary_roles:
        group, _ = Group.objects.get_or_create(name=role_name)
        group_map[role_name] = group

    # 2. Standardize existing user roles and assign group memberships
    for user in UserAccount.objects.all():
        if user.role == 'TEACHER':
            user.role = 'FACULTY'
            user.save(update_fields=['role'])
        elif user.role == 'OFFICE':
            user.role = 'OFFICE_STAFF'
            user.save(update_fields=['role'])

        # Associate user with primary role group
        target_group = group_map.get(user.role)
        if target_group:
            user.groups.add(target_group)


def reverse_standardization(apps, schema_editor):
    UserAccount = apps.get_model('accounts', 'UserAccount')
    for user in UserAccount.objects.all():
        if user.role == 'FACULTY':
            user.role = 'TEACHER'
            user.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrator'),
                    ('FACULTY', 'Faculty'),
                    ('OFFICE_STAFF', 'Office Staff'),
                    ('STUDENT', 'Student'),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(
            initialize_groups_and_standardize_roles,
            reverse_code=reverse_standardization,
        ),
    ]

