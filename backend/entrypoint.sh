#!/usr/bin/env bash
set -e

echo "[entrypoint] Chờ cơ sở dữ liệu sẵn sàng..."
python - <<'PY'
import os, time, sys
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL", "")
if not url:
    print("[entrypoint] Thiếu DATABASE_URL"); sys.exit(1)

for attempt in range(1, 61):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"[entrypoint] Kết nối DB thành công (lần thử {attempt}).")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"[entrypoint] DB chưa sẵn sàng ({attempt}/60): {exc}")
        time.sleep(2)
else:
    print("[entrypoint] Không kết nối được DB, thoát."); sys.exit(1)
PY

echo "[entrypoint] Chạy migration..."
flask --app wsgi db upgrade

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Seed dữ liệu mẫu..."
  flask --app wsgi seed || true
fi

if [ "${CREATE_ADMIN_ON_START:-true}" = "true" ]; then
  echo "[entrypoint] Bảo đảm tài khoản quản trị..."
  flask --app wsgi create-admin || true
fi

echo "[entrypoint] Khởi động ứng dụng: $*"
exec "$@"
