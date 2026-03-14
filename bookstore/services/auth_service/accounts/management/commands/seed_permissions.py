"""
python manage.py seed_permissions

Tạo toàn bộ Role, Permission, RolePermission vào DB.
Idempotent — chạy nhiều lần không duplicate.
"""
from django.core.management.base import BaseCommand
from accounts.models import Role, Permission, RolePermission
from accounts.permissions import PERMISSION_MATRIX, ROLE_PERMISSIONS


class Command(BaseCommand):
    help = 'Seed roles and permissions into the database'

    def handle(self, *args, **options):
        self.stdout.write('🔐 Seeding roles and permissions...\n')

        # ── 1. Tạo Permissions từ PERMISSION_MATRIX ──────────────────────────
        perm_count = 0
        for service, resources in PERMISSION_MATRIX.items():
            for resource, actions in resources.items():
                for action, description in actions.items():
                    codename = f"{service}:{resource}:{action}"
                    _, created = Permission.objects.get_or_create(
                        codename=codename,
                        defaults={
                            'name':        description,
                            'service':     service,
                            'resource':    resource,
                            'action':      action,
                            'description': description,
                        }
                    )
                    if created:
                        perm_count += 1

        self.stdout.write(f'  ✅ {perm_count} permissions created\n')

        # ── 2. Tạo Roles ──────────────────────────────────────────────────────
        ROLE_META = {
            'customer': 'Khách hàng mua sách',
            'seller':   'Nhà sách / người bán',
            'author':   'Tác giả sách',
            'admin':    'Quản trị viên nền tảng',
        }
        role_count = 0
        for name, desc in ROLE_META.items():
            _, created = Role.objects.get_or_create(
                name=name,
                defaults={'display_name': name.title(), 'description': desc}
            )
            if created:
                role_count += 1

        self.stdout.write(f'  ✅ {role_count} roles created\n')

        # ── 3. Gán Permissions vào Roles ──────────────────────────────────────
        rp_count = 0
        for role_name, codenames in ROLE_PERMISSIONS.items():
            role = Role.objects.get(name=role_name)
            for codename in codenames:
                try:
                    perm = Permission.objects.get(codename=codename)
                    _, created = RolePermission.objects.get_or_create(role=role, permission=perm)
                    if created:
                        rp_count += 1
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Permission not found: {codename}')
                    )

        self.stdout.write(f'  ✅ {rp_count} role-permissions linked\n')
        self.stdout.write(self.style.SUCCESS('\n🎉 Seeding complete!\n'))

        # ── Summary ───────────────────────────────────────────────────────────
        for role in Role.objects.all():
            count = role.role_permissions.count()
            self.stdout.write(f'  {role.name:<12} → {count} permissions')
