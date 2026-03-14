import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password',   models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('email',      models.EmailField(max_length=255, unique=True)),
                ('username',   models.CharField(max_length=50, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=50)),
                ('last_name',  models.CharField(blank=True, max_length=50)),
                ('avatar',     models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('bio',        models.TextField(blank=True, max_length=500)),
                ('phone',      models.CharField(blank=True, max_length=15)),
                ('is_active',  models.BooleanField(default=True)),
                ('is_staff',   models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(
                    blank=True, related_name='user_set', related_query_name='user',
                    to='auth.group', verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True, related_name='user_set', related_query_name='user',
                    to='auth.permission', verbose_name='user permissions',
                )),
            ],
            options={
                'db_table': 'users',
                'ordering': ['-date_joined'],
            },
            managers=[
                ('objects', django.contrib.auth.models.BaseUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email',      models.EmailField()),
                ('ip_address', models.GenericIPAddressField(null=True)),
                ('success',    models.BooleanField(default=False)),
                ('timestamp',  models.DateTimeField(auto_now_add=True)),
                ('user_agent', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'login_attempts',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='users_username_idx'),
        ),
        migrations.AddIndex(
            model_name='loginattempt',
            index=models.Index(fields=['email', 'timestamp'], name='login_email_ts_idx'),
        ),
    ]
