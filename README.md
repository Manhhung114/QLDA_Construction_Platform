# QLDA Construction Platform

Nền tảng **Construction Project Management** mới, chạy độc lập với hệ thống QLDA hiện tại. V1 triển khai đủ 12 nhóm module trên một mô hình dữ liệu chung, có đăng nhập JWT, PostgreSQL riêng, audit trail, upload file, workflow, dashboard, automation và risk summary.

## 12 module V1

| # | Module | Chức năng đã có trong V1 |
|---|---|---|
| 1 | Project & Portfolio | Dự án, ngân sách, thời gian, PM, trạng thái; API portfolio tổng hợp sức khỏe từng dự án |
| 2 | Task & WBS | WBS, task, assignee, priority, deadline, baseline, progress, predecessor |
| 3 | Schedule | Activity, planned/actual dates, milestone, progress, critical flag, predecessor IDs |
| 4 | Resource & Time | Resource, capacity, cost rate, timesheet |
| 5 | BOQ & Cost Control | BOQ, budget, actual quantity/amount, cost entries, variance dashboard |
| 6 | Contract & Procurement | Contract, contractor, value, duration; tự tính end date từ start date + duration; procurement orders |
| 7 | Document Control | Document number, discipline, revision, status, upload file; lịch sử document revisions |
| 8 | Quality | RFI, NCR, INS, Material, Test, Work Inspection dùng chung workflow trạng thái |
| 9 | Change Management | VO/change, cost impact, time impact, submitted/approved dates |
| 10 | Collaboration | Comment theo entity, notifications |
| 11 | Dashboard & BI | Task overdue, hồ sơ chờ, quality mở, VO chờ, budget/actual/variance, contract value, portfolio summary |
| 12 | Automation & AI | Workflow rules, cảnh báo task/quality quá hạn, hợp đồng sắp hết hạn; deterministic AI-style risk summary |

Ngoài 12 module còn có **User/Auth, file storage và immutable Audit Log** làm lớp nền tảng.

## Kiến trúc

```text
Browser
   |
   v
Next.js :3000
   |  /api/* rewrite
   v
FastAPI :8000 ---- /uploads
   |
   v
PostgreSQL
```

Trên VPS, Docker Compose chỉ bind frontend/backend vào `127.0.0.1`, vì vậy có thể đặt Nginx hiện có phía trước mà không mở port mới ra Internet.

## Chạy trên VPS để kiểm tra bản mới

```bash
git clone https://github.com/Manhhung114/QLDA_Construction_Platform.git
cd QLDA_Construction_Platform
cp .env.example .env
nano .env
# Đổi POSTGRES_PASSWORD, JWT_SECRET, ADMIN_PASSWORD trước khi chạy.
docker compose up -d --build
```

Kiểm tra:

```bash
docker compose ps
curl http://127.0.0.1:8100/health
curl -I http://127.0.0.1:3001
```

### Nginx cho subdomain beta

Ví dụ dùng `beta.tenmien.vn` trỏ cùng IP VPS:

```nginx
server {
    listen 80;
    server_name beta.tenmien.vn;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Sau đó cấp SSL bằng công cụ/cấu hình SSL đang dùng trên VPS. Không cần thay đổi site production hiện tại.

## Đăng nhập lần đầu

Tài khoản quản trị được tạo tự động ở lần khởi động đầu theo:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<giá trị trong .env>
```

Không sử dụng mật khẩu mặc định khi đưa subdomain beta ra Internet.

## API chính

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/users` — admin
- `GET|POST /api/data/{module}`
- `GET|PATCH|DELETE /api/data/{module}/{id}`
- `POST /api/files/upload`
- `GET /api/dashboard/summary`
- `GET /api/portfolio/summary`
- `POST /api/workflow/transition`
- `POST /api/automation/run`
- `GET /api/ai/risk-summary?project_id=...`
- `GET /docs` — Swagger của FastAPI (qua backend port nội bộ hoặc cấu hình Nginx riêng khi cần)

Các data endpoint hỗ trợ: `projects`, `wbs`, `tasks`, `schedule`, `resources`, `timesheets`, `boq`, `costs`, `contracts`, `procurement`, `documents`, `document-revisions`, `quality`, `changes`, `comments`, `notifications`, `workflow-rules`, `audit-logs`.

## Quy tắc dữ liệu

- Hệ thống mới dùng **database và Docker volumes riêng** (`qlda_new_pgdata`, `qlda_new_uploads`).
- Không kết nối hoặc ghi vào database của QLDA cũ.
- Mọi create/update/delete qua generic data API đều ghi `audit_logs`.
- `audit-logs` không cho sửa/xóa qua API.
- Contract tự suy ra `end_date = start_date + duration_days` nếu người dùng chưa nhập ngày kết thúc.
- File upload được lưu ở volume riêng và trả URL `/uploads/...`.

## Trạng thái V1

V1 là **functional beta của đủ 12 module**, phù hợp để chạy ở subdomain beta, nhập dữ liệu mẫu và chốt workflow/nghiệp vụ thực tế trước khi thay production. Trước khi dùng production diện rộng nên bổ sung schema migrations versioned, backup tự động, test suite/CI, granular RBAC theo project, virus scanning cho file, object storage và monitoring.
