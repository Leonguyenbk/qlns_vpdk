# Database migration

The backend uses the PostgreSQL database from `DATABASE_URL`. For a new empty Supabase database, run both migrations in order from the `backend` directory after reviewing the target database:

```powershell
psql "$env:DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/000_initial_schema.sql
psql "$env:DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/001_danh_muc_chuc_vu_gioi_han.sql
```

`000_initial_schema.sql` creates the baseline tables required by the current backend. `001_danh_muc_chuc_vu_gioi_han.sql` is additive and does not rewrite existing tables or data: it adds the nullable `chuc_vu.ma_chuc_vu` column, its unique partial index, and the `gioi_han_chuc_vu_don_vi` table with foreign keys, uniqueness, validation, and lookup indexes.

Do not use `db.create_all()` as a schema upgrade mechanism. Existing records without a position code are intentionally left unchanged and can be reviewed through `GET /api/chuc-vu/chua-co-ma`.