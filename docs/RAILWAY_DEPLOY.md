# Railway deployment — QLDA V2 Production Beta

Repo `Manhhung114/QLDA_Construction_Platform` được triển khai trên Railway theo mô hình 3 service trong **cùng một project và cùng environment**:

```text
Frontend (Next.js, public)
       |
       | Railway private network (HTTP)
       v
Backend (FastAPI, private)
    |             \
    v              v
PostgreSQL       Volume /data
```

## 1. Tạo project và services

Tạo một Railway project mới cho bản thử nghiệm, ví dụ `QLDA-Beta`, sau đó tạo:

1. **Postgres** bằng Railway PostgreSQL service.
2. **Backend** từ GitHub repo `Manhhung114/QLDA_Construction_Platform`.
   - Branch: `main`
   - Root Directory: `/backend`
3. **Frontend** từ cùng repo.
   - Branch: `main`
   - Root Directory: `/frontend`

Không tạo public domain cho Postgres. Backend cũng có thể giữ private-only. Chỉ Frontend cần public domain cho người dùng thử nghiệm.

## 2. Backend variables

Trong service **Backend**, cấu hình:

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

Nên **seal** các biến `JWT_SECRET` và `ADMIN_PASSWORD` sau khi kiểm tra đúng giá trị.

### Persistent file storage

Gắn Railway Volume vào Backend với mount path:

```text
/data
```

Ứng dụng lưu file tại `/data/uploads`. Không dùng filesystem tạm của container làm nơi lưu hồ sơ lâu dài.

### Backend startup

Docker image dùng `backend/start.sh`:

```text
alembic upgrade head
uvicorn app.final:app --host 0.0.0.0 --port $PORT --proxy-headers
```

Railway inject biến `PORT`; backend đã đọc biến này tự động.

Healthcheck:

```text
/health
```

Readiness:

```text
/ready
```

## 3. Frontend variables

Trong service **Frontend**:

```env
BACKEND_URL=http://${{Backend.RAILWAY_PRIVATE_DOMAIN}}:${{Backend.PORT}}
NODE_ENV=production
```

`BACKEND_URL` là biến server-side của Next.js. Browser không gọi private domain trực tiếp; Next.js rewrite các đường dẫn `/api/*`, `/uploads/*` và `/health` sang Backend.

Private networking của Railway dùng **HTTP**, không dùng HTTPS giữa Frontend và Backend.

Frontend healthcheck:

```text
/health
```

Sau khi Frontend deploy thành công, chọn **Networking → Generate Domain** để tạo URL beta public.

## 4. Thứ tự deploy

1. Postgres chuyển sang trạng thái healthy.
2. Backend build/deploy thành công.
3. Kiểm tra Backend healthcheck `/health` và readiness `/ready`.
4. Frontend build/deploy thành công.
5. Generate public domain cho Frontend.
6. Mở URL Frontend và đăng nhập bằng `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
7. Chạy acceptance checklist bên dưới.

## 5. Railway beta acceptance checklist

- Login/logout và tạo user.
- Tạo Project và phân project members/roles.
- Kiểm tra member không đọc được dữ liệu dự án không được phân quyền.
- WBS, Task, dependency, checklist, Kanban kéo-thả.
- Schedule, Gantt, CPM/critical path, milestone.
- Calendar tổng hợp deadline/milestone/hợp đồng.
- Resources, assignments, timesheet, workload.
- BOQ, budget version, cost entries, import XLSX/CSV, export CSV.
- Contract, automatic end date, payment certificate, procurement.
- Document/revision/transmittal, file upload, approve/reject và approval history.
- RFI/NCR/INS/material/test/work inspection.
- VO + Claim.
- Comments, notifications, audit logs.
- Dashboard + Portfolio health + global search.
- Built-in alerts, saved Workflow Rules, Risk Summary.
- Upload một file thử, redeploy Backend và xác nhận file vẫn còn trên Volume.
- Restart Backend và xác nhận Alembic không tạo lỗi migration.

## 6. Beta và Production phải tách environment

Dùng Railway environment riêng cho beta/staging. Khi nghiệm thu xong mới tạo/clone sang environment `production` với:

- PostgreSQL riêng.
- Volume riêng.
- Secret riêng.
- Public domain production riêng.

Không chuyển dữ liệu thật vào beta mặc định.

## 7. Các điểm Railway quan trọng

- Monorepo dùng Root Directory `/backend` và `/frontend` cho hai service độc lập.
- Dùng Railway reference variables thay vì hard-code hostname/password database.
- Frontend → Backend dùng private domain để tránh public exposure và service-to-service egress.
- Postgres giữ private mặc định; chỉ bật TCP Proxy nếu thật sự cần truy cập DB từ bên ngoài Railway.
- Healthcheck phải pass trước khi coi deploy là đạt.
- Railway database vẫn cần chính sách backup/restore riêng trước khi dùng production.

## 8. Sau khi deploy

Ghi lại các thông tin sau vào biên bản beta (không commit secret vào GitHub):

```text
Railway Project:
Environment:
Frontend Service:
Frontend Public URL:
Backend Service:
Postgres Service:
Volume mount: /data
Deployed Git SHA:
Acceptance result:
```
