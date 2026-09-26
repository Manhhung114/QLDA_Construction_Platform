# Railway deployment — QLDA V2 Production Beta

V2 được thiết kế để chạy trên Railway theo mô hình 3 service trong cùng một project/environment:

```text
Frontend (Next.js, public)
       |
       | Railway private network
       v
Backend (FastAPI, private)
    |             \
    v              v
PostgreSQL       Volume /data
```

## 1. Tạo services

Trong Railway tạo:

1. PostgreSQL.
2. Backend từ GitHub repo `Manhhung114/QLDA_Construction_Platform`, Root Directory `/backend`.
3. Frontend từ cùng repo, Root Directory `/frontend`.

Ở giai đoạn beta chọn branch `v2-production-beta`. Khi nghiệm thu và merge thì đổi production source sang `main`.

## 2. Backend variables

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
JWT_SECRET=<chuỗi bí mật ngẫu nhiên dài>
JWT_EXPIRE_HOURS=12
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<mật khẩu mạnh>
ADMIN_EMAIL=<email quản trị>
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_MB=50
MAX_IMPORT_MB=20
ALLOWED_UPLOAD_EXTENSIONS=.pdf,.xlsx,.xls,.csv,.doc,.docx,.jpg,.jpeg,.png,.dwg,.zip
CORS_ORIGINS=https://${{Frontend.RAILWAY_PUBLIC_DOMAIN}}
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

Gắn Railway Volume vào Backend với mount path:

```text
/data
```

Nếu không có volume, file upload không nên được xem là lưu trữ bền vững.

Backend start script chạy:

```text
alembic upgrade head
uvicorn app.final:app --host 0.0.0.0 --port $PORT --proxy-headers
```

Healthcheck path:

```text
/health
```

Readiness endpoint:

```text
/ready
```

## 3. Frontend variables

```env
BACKEND_URL=http://${{Backend.RAILWAY_PRIVATE_DOMAIN}}:${{Backend.PORT}}
NODE_ENV=production
```

`BACKEND_URL` chỉ được dùng ở Next.js server để rewrite `/api`, `/uploads` và `/health`; không cần public backend URL trong browser.

Frontend healthcheck:

```text
/
```

Generate public domain cho Frontend. Backend có thể giữ private-only.

## 4. Thứ tự deploy

1. Postgres healthy.
2. Backend deploy thành công và `/health` trả `status=ok`.
3. Frontend deploy thành công.
4. Mở public domain Frontend.
5. Đăng nhập bằng `ADMIN_USERNAME`/`ADMIN_PASSWORD`.
6. Chạy checklist beta bên dưới.

## 5. Railway beta acceptance checklist

- Login/logout và tạo users.
- Project + project members/roles.
- WBS, Task, dependency, checklist, Kanban drag/drop.
- Schedule, Gantt, CPM/critical path, milestone.
- Calendar.
- Resources, assignments, timesheet, workload.
- BOQ, budget version, cost entries, import XLSX/CSV, export CSV.
- Contract, automatic end date, payment certificate, procurement.
- Document/revision/transmittal, file upload, approve/reject history.
- RFI/NCR/INS/material/test/work inspection.
- VO + Claim.
- Comments, notifications, audit logs.
- Dashboard + Portfolio health + global search.
- Built-in alerts, saved Workflow Rules, Risk Summary.
- Redeploy Backend rồi xác nhận file upload vẫn tồn tại trên Volume.

## 6. Không dùng dữ liệu beta làm production mặc định

Nên tạo Railway environment `production` riêng, với PostgreSQL và Volume riêng. Chỉ chuyển dữ liệu thật sau khi beta được nghiệm thu, CI xanh và migration đã được thử trên bản sao dữ liệu.

## 7. Railway configuration note

Với project/service Railway mới, cấu hình deployment trực tiếp trong Railway UI/CLI/Infrastructure-as-Code hiện hành. Không cần tạo `railway.toml` hoặc `railway.json` mới chỉ để cấu hình root directory/healthcheck cho bản beta này.
