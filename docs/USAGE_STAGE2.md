# راهنمای استفاده (USAGE) ـ مرحله ۲: پشت میز DBA (نسخه 0.2.0)

در این نسخه، بارگذاری داده از **پکیج مرحله ۱** (`nyc311_factory`) انجام می‌شود. مرحله ۲ فقط این‌ها را دارد: مشخصات جدول‌ها، رابطه بین جدول‌ها، فایل‌های `sql` و تحلیل‌ها.

> بخش‌های مربوط به `PostgreSQL` در ماشین من اجرا نشده‌اند (فقط تست‌های بدون دیتابیس اجرا شدند). اولین اجرای واقعی را خودت انجام بده.

## ۱. جریان کار

1. `prepare_inputs`: آماده‌سازی چند فایل (تغییر نام دو سرستون، افزودن دسته‌های گم‌شده به جدول ترجمه، میانگین‌گیری `geolocation` بر اساس کد پستی).
2. اجرای فایل‌های `sql` ساختار: schemaها، جدول‌ها، جدول‌های قرنطینه.
3. خالی کردن جدول‌ها (`TRUNCATE`)، تا اجرای دوباره همان نتیجه را بدهد و تکراری نسازد.
4. برای هر جدول به ترتیب وابستگی، یک اجرای `run_pipeline` پکیج ۱ با مقصد `database`:
   - اعتبارسنجی با `Contract`
   - بررسی کلید خارجی با `in_keys_rule` (ردیف یتیم با کد `FK_...` به قرنطینه می‌رود)
   - ردیف تکراری با `DUPLICATE_KEY`
   - نوشتن در جدول با حالت `existing` (کلید و ایندکس شما می‌ماند)
   - `manifest_run.json` و `quality_report.json` برای همان جدول
5. اجرای `View`، `Function`، `Procedure` و `Index`.

نکته: مقصد `database` پکیج ۱ فایل میانی نمی‌سازد؛ داده در یک جدول موقت (`..__staging`) می‌نشیند و بعد جایگزین می‌شود. اگر فایل `CSV` هم می‌خواهی، `"csv"` را به `destinations` اضافه کن.

## ۲. نصب و اجرا

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ..\stage-1-zahra-jafarii
pip install -r requirements.txt
pip install -e .
python -m data_factory.cli
python -m unittest discover tests
```

گزینه‌ها: `--raw-dir` (پوشه CSVها)، `--work-dir` (پوشه فایل‌های آماده و `manifest`ها)، `--stage1-config` (بخش ۷).

## ۳. ساختار دیتابیس

| شیء | نام | توضیح |
|---|---|---|
| schema | `olist` | جدول‌های Olist |
| schema | `stage1` | خروجی پکیج مرحله ۱ (بخش ۷) |
| جدول داده | `category_translation`، `customers`، `sellers`، `products`، `orders`، `order_items`، `order_payments`، `order_reviews`، `geolocation` | `geolocation` یک ردیف برای هر کد پستی |
| جدول قرنطینه | `<نام جدول>_quarantine` | همه ستون‌ها به‌صورت متن + `reason_codes` |
| `View` | `v_quarantine` | همه قرنطینه‌ها در یک جا: `source_table`، `reason_codes`، `raw_record` |
| `View` | `v_delivered_orders`، `v_order_items_enriched` | ساده و چندجدولی |
| `Function` | `olist.delivery_delay_days` | تأخیر تحویل به روز |
| `Procedure` | `olist.rebuild_monthly_snapshot(ماه)` | idempotent |
| جدول | `benchmark_results`، `monthly_category_snapshot` | اندازه‌گیری و snapshot |

## ۴. وظیفه هر فایل

### پایتون (`src/data_factory/`)

| فایل | وظیفه | کجا استفاده می‌شود |
|---|---|---|
| `config.py` | مسیرها، `seed`، اندازه batch، آستانه قرنطینه، آدرس دیتابیس | همه |
| `contracts.py` | نام فایل‌ها، تغییر نام سرستون، ترتیب بارگذاری، روابط کلید خارجی | `prepare`، `olist_datasets`، `profiling` |
| `olist_datasets.py` | `Contract` هر جدول (نوع، خالی‌نبودن، دامنه، کلید) و قانون کلید خارجی؛ ساخت `Dataset` برای پکیج ۱ | `olist_load` |
| `keys.py` | فراهم کردن کلیدهای جدول والد (از دیتابیس یا از پوشه) | `olist_load`، `cli` |
| `prepare.py` | آماده‌سازی ورودی‌ها پیش از پکیج ۱ | `cli` |
| `olist_load.py` | ساخت `Config` هر جدول، اجرای `run_pipeline`، جدول خلاصه | `cli`، تست |
| `db.py` | engine، اجرای فایل `sql`، خواندن دسته‌ای، شمارش، `TRUNCATE`، نوشتن `DataFrame` با نوع مشخص | همه |
| `cli.py` | `build_database` و `load_stage1_output` | خط فرمان، نوتبوک |
| `benchmark.py`، `index_lab.py`، `snapshots.py` | زمان‌گیری، آزمایش `Index`، ساخت snapshot | نوتبوک |
| `profiling.py` | یتیم‌ها، کلید تکراری، مقدار خالی در داده خام | نوتبوک |

### `sql` (`src/data_factory/sql/`، داخل پکیج، پس بعد از نصب هم در دسترس است)

| فایل | وظیفه |
|---|---|
| `001_schemas.sql` | schemaها |
| `002_tables.sql` | جدول‌های داده |
| `002_quarantine_tables.sql` | جدول‌های قرنطینه (با تست همگام با `Contract`ها) |
| `002_benchmark_tables.sql` | `benchmark_results` |
| `003_views.sql` | `View`ها |
| `004_functions.sql`، `005_procedures.sql` | `Function` و `Procedure` |
| `006_indexes.sql` | `Index`های نهایی (خروجی نوتبوک) |
| `candidate_indexes.sql`، `queries/` | نامزدهای `Index` و کوئری‌ها |

## ۵. خروجی‌ها

| خروجی | کجا | چه چیزی را نشان می‌دهد |
|---|---|---|
| جدول خلاصه | چاپ `python -m data_factory.cli` و نوتبوک | `read`، `inserted`، `quarantined` و دلیل‌ها برای هر جدول |
| `curated/olist/<جدول>/manifest_run.json` | پوشه `--work-dir` (پیش‌فرض `curated/`) | شمارش و دلیل‌های قرنطینه آن جدول |
| `curated/olist/<جدول>/quality_report.json` | همان‌جا | آمار ستون‌ها |
| `curated/olist/load_summary.json` | همان‌جا | خلاصه همه جدول‌ها |
| `curated/prepared/` | همان‌جا | فایل‌های آماده‌شده (سرستون عوض‌شده، ترجمه کامل، `geolocation` تجمیعی) |
| جدول‌های `*_quarantine` و `v_quarantine` | دیتابیس | ردیف‌های ردشده و دلیلشان |

مثال: شمارش هر دلیل قرنطینه

```sql
SELECT source_table, reason_code, COUNT(*)
FROM (SELECT source_table, unnest(string_to_array(reason_codes, '|')) AS reason_code
      FROM olist.v_quarantine) AS reasons
GROUP BY 1, 2 ORDER BY 1, 2;
```

## ۶. اضافه کردن داده یک منبع دیگر (مثل خروجی پکیج ۱)

الگوی کلی برای هر دیتاست تازه:

1. `Contract` و `Dataset` بنویس (در پروژه خودت).
2. جدول (و جدول قرنطینه‌اش با ستون‌های منبع + `reason_codes`) را در یک فایل `.sql` بساز.
3. کانفیگ: `destinations: ["database"]`، `database_schema`، `database_load_mode: "existing"`.
4. `run_pipeline(config, dataset=DATASET)`، با `DATABASE_URL` برابر دیتابیس مرحله ۲.

## ۷. ریختن خروجی پکیج ۱ (NYC) در `stage1`

در کانفیگ پکیج ۱ (یا با `overrides`) این‌ها را بگذار:

```json
{
  "destinations": ["csv", "database"],
  "database_schema": "stage1",
  "database_cases_table": "cases",
  "database_quarantine_table": "quarantine",
  "database_load_mode": "replace"
}
```

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://olist_user:olist_pass@localhost:5432/olist"
python -m data_factory.cli --stage1-config ..\stage-1-zahra-jafarii\config.json
```

- با `replace`، جدول از `Contract` ساخته می‌شود. اگر می‌خواهی `DDL` در گیت باشد، جدول را در `sql/007_stage1_tables.sql` بنویس و `existing` بگذار (ستون‌ها باید با خروجی بخوانند).
- یک بار اجرا و `SELECT COUNT(*) FROM stage1.cases` را بررسی کن؛ اجرای دوم نباید تعداد را عوض کند.

## ۸. استفاده در مرحله ۳ و چالش نهایی

- مرحله ۳: همین دیتابیس و همان `DATABASE_URL`، schema جدا (`stage3`).
- چالش نهایی:

```python
from data_factory.cli import build_database
summary = build_database(raw_dir="data/raw/olist", work_dir="data/curated")
```

  - فایل‌های `sql` این پکیج بعد از نصب در `data_factory.config.SQL_DIR` هستند.
  - ویژگی‌های چالش نهایی در `schema` و فایل‌های `sql` خودش ساخته می‌شوند، نه با ویرایش این پکیج.
  - هنگام ممیزی زمانی ستون‌ها این اشیا را با دقت بررسی کن، چون اطلاعات پس از لحظه تأیید سفارش دارند: `v_delivered_orders`، ستون `order_status` در `v_order_items_enriched`، `delivery_delay_days`، `monthly_category_snapshot`.
- قاعده: مراحل بعد کد این پکیج را ویرایش نمی‌کنند؛ اگر چیزی لازم شد، نسخه جدید و تگ.

## ۹. خطاهای رایج

| علامت | علت محتمل |
|---|---|
| `ModuleNotFoundError: nyc311_factory` | پکیج مرحله ۱ نصب نشده یا نسخه قدیمی است |
| خروج با کد ۶ (`QuarantineThresholdError`) | نسبت قرنطینه یک جدول از آستانه بالاتر رفته؛ `manifest_run.json` آن جدول را ببین |
| `relation "olist.xxx_quarantine" does not exist` | فایل `002_quarantine_tables.sql` اجرا نشده |
| `connection refused` / `role does not exist` | PostgreSQL یا کاربر ساخته نشده |
| `FileNotFoundError` | فایل CSV در `raw/` نیست |
