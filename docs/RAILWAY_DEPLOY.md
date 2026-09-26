# Chạy thử QLDA V2 trên Railway

> Tài liệu này theo Railway hiện hành (09/2026). Với project Railway mới, không dùng `railway.toml/railway.json` mới vì Config as Code đã deprecated; cấu hình service bằng Railway dashboard/CLI hoặc Infrastructure as Code mới của Railway.

## Kiến trúc

```text
Internet
   |
   v
Frontend (Next.js, public domain)
   |
   | BACKEND_URL qua Railway private network
   v
Backend (FastAPI, private)
   |              \
   v               v
PostgreSQL       Volume /data
                 uploads persistent
```

Backend không cần public domain: browser gọi `/api/*` trên Frontend, Next.js rewrite sang Backend qua private network.

## 1. Tạo Railway project

Tạo **Empty Project**. Trong cùng environment tạo 3 service:

1. `Postgres` — Railway PostgreSQL.
2. `Backend` — GitHub repo `Manhhung114/QLDA_Construction_Platform`, Root Directory `/backend`.
3. `Frontend` — cùng repo, Root Directory `/frontend`.

Mỗi service source dùng branch cần chạy thử (`v2-production-beta` khi beta, sau này `main`). Dockerfile trong từng root directory sẽ được Railway tự nhận diện.

## 2. Backend variables

Thiết lập trong service `Backend`:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
JWT_SECRET=<chuỗi ngẫu nhiên dài, không dùng giá trị mẫu>
JWT_EXPIRE_HOURS=12
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<mật khẩu mạnh riêng cho beta>
ADMIN_EMAIL=<email quản trị>
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_MB=50
ALLOWED_UPLOAD_EXTENSIONS=.pdf,.xlsx,.xls,.csv,.doc,.docx,.jpg,.jpeg,.png,.dwg,.zip
CORS_ORIGINS=https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

`DATABASE_URL` của Railway được backend tự normalize sang SQLAlchemy psycopg URL.

### Volume

Gắn Railway Volume cho `Backend`, mount path:

```text
/data
```

Nếu không gắn volume, file upload nằm trên ephemeral filesystem và có thể mất sau redeploy.

### Healthcheck

Backend Settings -> Healthcheck Path:

```text
/health
```

Backend Docker start script tự chạy:

```text
alembic upgrade head
uvicorn app.v2:app --host 0.0.0.0 --port $PORT
```

## 3. Frontend variables

Trong service `Frontend`:

```env
BACKEND_URL=http://${{Backend.RAILWAY_PRIVATE_DOMAIN}}:${{Backend.PORT}}
NODE_ENV=production
```

Không dùng `NEXT_PUBLIC_BACKEND_URL`: backend private URL chỉ cần Next.js server biết, không đưa vào bundle trình duyệt.

Frontend Settings -> Healthcheck Path:

```text
/
```

Sau khi deploy, tạo public domain cho **Frontend**. Backend có thể giữ private-only.

## 4. Thứ tự deploy lần đầu

1. Postgres healthy.
2. Deploy Backend và kiểm tra `/health` trong deployment logs/healthcheck.
3. Deploy Frontend.
4. Generate public domain cho Frontend.
5. Mở app, đăng nhập bằng `ADMIN_USERNAME` / `ADMIN_PASSWORD` đã khai báo.
6. Tạo project thử, task, hồ sơ; chạy workflow; upload file; kiểm tra dashboard và audit log.

## 5. Checklist nghiệm thu beta

- Login / logout.
- Tạo Project và Project Members.
- Task, WBS, dependency, checklist.
- Schedule và milestone.
- Resource assignment, timesheet, workload.
- BOQ, budget version, cost entry.
- Contract, payment certificate, procurement.
- Document, revision, transmittal và workflow approve/reject.
- RFI/NCR/INS/material/test/work inspection.
- VO và Claim.
- Comment, notification, audit log.
- Dashboard/Portfolio.
- Automation cảnh báo và Risk Summary.
- CSV export.
- Upload file vẫn còn sau redeploy Backend (kiểm tra volume).

## 6. Khi chuyển từ beta sang production

- Tạo Railway environment `production` riêng với Postgres/volume riêng.
- Đổi toàn bộ secret và admin password.
- Chỉ autodeploy `main` sau khi GitHub CI xanh.
- Backup PostgreSQL trước migration lớn.
- Không dùng database beta làm production nếu dữ liệu beta chỉ là dữ liệu thử.
