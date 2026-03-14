import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [

        # ── Role ──────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',         models.CharField(max_length=20, unique=True,
                                  choices=[('customer','Customer'),('seller','Seller'),
                                           ('author','Author'),('admin','Admin')])),
                ('display_name', models.CharField(max_length=50)),
                ('description',  models.TextField(blank=True)),
                ('is_active',    models.BooleanField(default=True)),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'roles'},
        ),

        # ── Permission ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('codename',    models.CharField(max_length=100, unique=True)),
                ('name',        models.CharField(max_length=200)),
                ('service',     models.CharField(max_length=30)),
                ('resource',    models.CharField(max_length=50)),
                ('action',      models.CharField(max_length=30)),
                ('description', models.TextField(blank=True)),
            ],
            options={'db_table': 'permissions', 'ordering': ['service', 'resource', 'action']},
        ),

        # ── RolePermission ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('role',       models.ForeignKey('accounts.Role',       on_delete=django.db.models.deletion.CASCADE, related_name='role_permissions')),
                ('permission', models.ForeignKey('accounts.Permission', on_delete=django.db.models.deletion.CASCADE, related_name='role_permissions')),
                ('granted_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'role_permissions', 'unique_together': {('role', 'permission')}},
        ),

        # ── UserRole ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user',        models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name='user_roles')),
                ('role',        models.ForeignKey('accounts.Role', on_delete=django.db.models.deletion.CASCADE, related_name='user_roles')),
                ('assigned_by', models.BigIntegerField(null=True, blank=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at',  models.DateTimeField(null=True, blank=True)),
            ],
            options={'db_table': 'user_roles', 'unique_together': {('user', 'role')}},
        ),

        # ── SellerProfile ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='SellerProfile',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user',             models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name='seller_profile')),
                ('business_name',    models.CharField(max_length=200, blank=True)),
                ('business_type',    models.CharField(max_length=50, blank=True)),
                ('tax_code',         models.CharField(max_length=50, blank=True)),
                ('id_card_number',   models.CharField(max_length=50, blank=True)),
                ('id_card_front',    models.ImageField(upload_to='kyc/id_cards/', blank=True, null=True)),
                ('id_card_back',     models.ImageField(upload_to='kyc/id_cards/', blank=True, null=True)),
                ('business_license', models.FileField(upload_to='kyc/licenses/', blank=True, null=True)),
                ('verify_status',    models.CharField(max_length=15, default='pending',
                                      choices=[('pending','Pending Review'),('approved','Approved'),('rejected','Rejected')])),
                ('verified_at',      models.DateTimeField(null=True, blank=True)),
                ('verified_by',      models.BigIntegerField(null=True, blank=True)),
                ('reject_reason',    models.TextField(blank=True)),
                ('bank_name',        models.CharField(max_length=100, blank=True)),
                ('bank_account',     models.CharField(max_length=50, blank=True)),
                ('bank_owner',       models.CharField(max_length=150, blank=True)),
                ('max_shops',        models.PositiveSmallIntegerField(default=3)),
                ('commission_rate',  models.DecimalField(max_digits=5, decimal_places=2, default=10.00)),
                ('created_at',       models.DateTimeField(auto_now_add=True)),
                ('updated_at',       models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'seller_profiles'},
        ),

        # ── AuthorProfile ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='AuthorProfile',
            fields=[
                ('id',                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user',               models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name='author_profile')),
                ('catalog_author_id',  models.BigIntegerField(null=True, blank=True)),
                ('pen_name',           models.CharField(max_length=200, blank=True)),
                ('nationality',        models.CharField(max_length=100, blank=True)),
                ('biography',          models.TextField(blank=True)),
                ('website',            models.URLField(blank=True)),
                ('facebook',           models.URLField(blank=True)),
                ('is_verified',        models.BooleanField(default=False)),
                ('verified_at',        models.DateTimeField(null=True, blank=True)),
                ('royalty_rate',       models.DecimalField(max_digits=5, decimal_places=2, default=10.00)),
                ('bank_name',          models.CharField(max_length=100, blank=True)),
                ('bank_account',       models.CharField(max_length=50, blank=True)),
                ('bank_owner',         models.CharField(max_length=150, blank=True)),
                ('created_at',         models.DateTimeField(auto_now_add=True)),
                ('updated_at',         models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'author_profiles'},
        ),
    ]
