# مرحله ۲: پشت میز DBA (داده‌ی Olist روی PostgreSQL)

این پروژه ۹ فایل `CSV` ی `Olist` را در `PostgreSQL` بارگذاری می‌کند، پنج کوئری تحلیلی را اندازه می‌گیرد و با شاهد پلن اجرا بهینه می‌کند.

## پیش‌نیاز

1. `PostgreSQL` نصب باشد و این دستورها در آن اجرا شده باشد:

```sql
CREATE USER olist_user WITH PASSWORD 'olist_pass';
CREATE DATABASE olist OWNER olist_user;
CREATE DATABASE olist_test OWNER olist_user;
```

2. فایل‌های `CSV` دیتاست `olistbr/brazilian-ecommerce` (از `Kaggle`) در پوشه‌ی `raw/` باشند.

## اجرا

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python -m data_factory.cli
python -m unittest discover tests
```

- فرمان `data_factory.cli` از دیتابیس خالی، جدول‌ها، داده، `View`ها، `Function`، `Procedure` و `Index`های تأییدشده را می‌سازد.
- نوتبوک `solution.ipynb` را با `Restart & Run All` اجرا کن. دیتابیس را خودش از صفر می‌سازد.
- آدرس دیتابیس با متغیر محیطی `DATABASE_URL` عوض می‌شود. پیش‌فرض: `postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist`
- تصمیم‌ها و عددها در `report.md` آمده است. هر عدد از یکی از بخش‌های نوتبوک می‌آید.