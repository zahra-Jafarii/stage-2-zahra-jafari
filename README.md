# مرحله ۲: پشت میز DBA

1. `PostgreSQL` را نصب کن و دو دیتابیس `olist` و `olist_test` را با کاربر `olist_user` بساز (دستورها در `report.md` نیست، در بخش پایین).
2. فایل‌های `CSV` دیتاست `Olist` را از `Kaggle` دانلود کن و در پوشه‌ی `raw/` بگذار.
3. محیط مجازی بساز: `python -m venv .venv` و فعالش کن.
4. نصب: `pip install -r requirements.txt` و بعد `pip install -e .`
5. ساخت کامل دیتابیس با یک فرمان: `python -m data_factory.cli`
6. تست‌ها: `python -m unittest discover tests`
7. نوتبوک: `solution.ipynb` را با `Restart & Run All` اجرا کن.
8. آدرس دیتابیس را می‌شود با متغیر محیطی `DATABASE_URL` عوض کرد.
9. دستور ساخت دیتابیس: `CREATE USER olist_user WITH PASSWORD 'olist_pass'` و `CREATE DATABASE olist OWNER olist_user`
10. نتیجه‌ی اندازه‌گیری‌ها و تصمیم‌ها در `report.md` آمده است.
