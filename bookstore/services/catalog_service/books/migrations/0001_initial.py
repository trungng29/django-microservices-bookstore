import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [

        # ── Author ────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id',          models.BigAutoField(primary_key=True, serialize=False)),
                ('name',        models.CharField(max_length=200)),
                ('slug',        models.SlugField(max_length=220, unique=True, blank=True)),
                ('bio',         models.TextField(blank=True)),
                ('avatar',      models.ImageField(upload_to='authors/', blank=True, null=True)),
                ('nationality', models.CharField(max_length=100, blank=True)),
                ('birth_date',  models.DateField(null=True, blank=True)),
                ('death_date',  models.DateField(null=True, blank=True)),
                ('website',     models.URLField(blank=True)),
                ('avg_rating',  models.DecimalField(max_digits=3, decimal_places=2, default=0.00)),
                ('total_books', models.PositiveIntegerField(default=0)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'authors', 'ordering': ['name']},
        ),
        migrations.AddIndex(
            model_name='author',
            index=models.Index(fields=['slug'], name='authors_slug_idx'),
        ),

        # ── Publisher ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id',         models.BigAutoField(primary_key=True, serialize=False)),
                ('name',       models.CharField(max_length=200, unique=True)),
                ('slug',       models.SlugField(max_length=220, unique=True, blank=True)),
                ('website',    models.URLField(blank=True)),
                ('email',      models.EmailField(blank=True)),
                ('country',    models.CharField(max_length=100, blank=True)),
                ('logo',       models.ImageField(upload_to='publishers/', blank=True, null=True)),
                ('founded_at', models.PositiveIntegerField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'publishers', 'ordering': ['name']},
        ),

        # ── Category ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id',          models.BigAutoField(primary_key=True, serialize=False)),
                ('parent',      models.ForeignKey('self', null=True, blank=True,
                                  on_delete=django.db.models.deletion.SET_NULL,
                                  related_name='children')),
                ('name',        models.CharField(max_length=100)),
                ('slug',        models.SlugField(max_length=120, unique=True, blank=True)),
                ('description', models.TextField(blank=True)),
                ('icon',        models.CharField(max_length=10, blank=True)),
                ('sort_order',  models.PositiveSmallIntegerField(default=0)),
                ('is_active',   models.BooleanField(default=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'categories', 'ordering': ['sort_order', 'name']},
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['slug'], name='categories_slug_idx'),
        ),

        # ── Book ──────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id',             models.BigAutoField(primary_key=True, serialize=False)),
                ('shop_id',        models.BigIntegerField(db_index=True)),
                ('publisher',      models.ForeignKey('Publisher', on_delete=django.db.models.deletion.SET_NULL,
                                    null=True, blank=True, related_name='books')),
                ('title',          models.CharField(max_length=300)),
                ('slug',           models.SlugField(max_length=320, unique=True, blank=True)),
                ('subtitle',       models.CharField(max_length=300, blank=True)),
                ('isbn',           models.CharField(max_length=13, unique=True, blank=True, null=True)),
                ('description',    models.TextField(blank=True)),
                ('pages',          models.PositiveIntegerField(null=True, blank=True)),
                ('language',       models.CharField(max_length=5, default='vi',
                                    choices=[('vi','Tiếng Việt'),('en','English'),('fr','Français'),
                                             ('ja','日本語'),('zh','中文'),('ko','한국어'),
                                             ('de','Deutsch'),('es','Español')])),
                ('book_format',    models.CharField(max_length=15, default='paperback',
                                    choices=[('paperback','Paperback'),('hardcover','Hardcover'),
                                             ('ebook','E-Book'),('audiobook','Audiobook')])),
                ('publish_date',   models.DateField(null=True, blank=True)),
                ('edition',        models.PositiveSmallIntegerField(default=1)),
                ('weight',         models.PositiveIntegerField(null=True, blank=True)),
                ('dimensions',     models.CharField(max_length=50, blank=True)),
                ('cover_image',    models.ImageField(upload_to='books/covers/', blank=True, null=True)),
                ('cover_thumb',    models.ImageField(upload_to='books/thumbs/', blank=True, null=True)),
                ('sample_pdf',     models.FileField(upload_to='books/samples/', blank=True, null=True)),
                ('avg_rating',     models.DecimalField(max_digits=3, decimal_places=2, default=0.00)),
                ('total_reviews',  models.PositiveIntegerField(default=0)),
                ('total_sold',     models.PositiveIntegerField(default=0)),
                ('stock_quantity', models.IntegerField(default=0)),
                ('is_active',      models.BooleanField(default=True)),
                ('is_featured',    models.BooleanField(default=False)),
                ('is_bestseller',  models.BooleanField(default=False)),
                ('created_at',     models.DateTimeField(auto_now_add=True)),
                ('updated_at',     models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'books', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='book', index=models.Index(fields=['slug'], name='books_slug_idx')),
        migrations.AddIndex(model_name='book', index=models.Index(fields=['isbn'], name='books_isbn_idx')),
        migrations.AddIndex(model_name='book', index=models.Index(fields=['shop_id'], name='books_shop_idx')),
        migrations.AddIndex(model_name='book', index=models.Index(fields=['is_active', 'is_featured'], name='books_active_featured_idx')),

        # ── BookAuthor ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='BookAuthor',
            fields=[
                ('id',         models.BigAutoField(primary_key=True, serialize=False)),
                ('book',       models.ForeignKey('Book',   on_delete=django.db.models.deletion.CASCADE, related_name='book_authors')),
                ('author',     models.ForeignKey('Author', on_delete=django.db.models.deletion.CASCADE, related_name='book_authors')),
                ('role',       models.CharField(max_length=20, default='author',
                                choices=[('author','Author'),('co_author','Co-Author'),
                                         ('editor','Editor'),('translator','Translator'),
                                         ('illustrator','Illustrator'),('foreword','Foreword by')])),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'db_table': 'book_authors', 'ordering': ['sort_order'],
                     'unique_together': {('book', 'author', 'role')}},
        ),

        # ── BookCategory ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='BookCategory',
            fields=[
                ('id',         models.BigAutoField(primary_key=True, serialize=False)),
                ('book',       models.ForeignKey('Book',     on_delete=django.db.models.deletion.CASCADE, related_name='book_categories')),
                ('category',   models.ForeignKey('Category', on_delete=django.db.models.deletion.CASCADE, related_name='book_categories')),
                ('is_primary', models.BooleanField(default=False)),
            ],
            options={'db_table': 'book_categories',
                     'unique_together': {('book', 'category')}},
        ),

        # ── BookPrice ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='BookPrice',
            fields=[
                ('id',             models.BigAutoField(primary_key=True, serialize=False)),
                ('book',           models.ForeignKey('Book', on_delete=django.db.models.deletion.CASCADE, related_name='prices')),
                ('original_price', models.DecimalField(max_digits=12, decimal_places=2)),
                ('sale_price',     models.DecimalField(max_digits=12, decimal_places=2)),
                ('discount_pct',   models.PositiveSmallIntegerField(default=0)),
                ('valid_from',     models.DateTimeField()),
                ('valid_to',       models.DateTimeField(null=True, blank=True)),
                ('is_active',      models.BooleanField(default=True)),
                ('created_by',     models.BigIntegerField()),
                ('created_at',     models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'book_prices', 'ordering': ['-valid_from']},
        ),
        migrations.AddIndex(model_name='bookprice', index=models.Index(fields=['book', 'is_active'], name='price_book_active_idx')),

        # ── BookImage ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='BookImage',
            fields=[
                ('id',         models.BigAutoField(primary_key=True, serialize=False)),
                ('book',       models.ForeignKey('Book', on_delete=django.db.models.deletion.CASCADE, related_name='images')),
                ('image',      models.ImageField(upload_to='books/gallery/')),
                ('alt_text',   models.CharField(max_length=200, blank=True)),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'db_table': 'book_images', 'ordering': ['sort_order']},
        ),
    ]
