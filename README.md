# QLDA Construction Platform — V1.0 Foundation

Nền tảng quản lý dự án xây dựng mới, tách độc lập với hệ thống QLDA cũ.

## 12 module
1. Project & Portfolio
2. Task & WBS
3. Schedule
4. Resource
5. BOQ & Cost
6. Contract & Procurement
7. Document Control
8. Quality (RFI/NCR/INS/Inspection)
9. Change Management (VO/Claim)
10. Collaboration
11. Dashboard & BI
12. Automation & AI-ready

## Kiến trúc
- Frontend: Next.js 16 + TypeScript
- Backend: FastAPI + SQLAlchemy 2
- Database: PostgreSQL 18
- Redis foundation
- JWT authentication
- Role foundation: admin / manager / member
- Audit trail cho create/update/delete
- Docker Compose, port riêng để chạy song song hệ thống cũ

## Khởi chạy
```bash
cp .env.example .env
# sửa toàn bộ password/secret trong .env
docker compose up --build -d
```

Frontend: `http://SERVER:3001`
Backend: `http://SERVER:8100`
Swagger: `http://SERVER:8100/docs`
Health: `http://SERVER:8100/health`

Tài khoản admin ban đầu được tạo từ `ADMIN_EMAIL` và `ADMIN_PASSWORD` trong `.env`; repo không chứa mật khẩu mặc định.

## API
CRUD foundation áp dụng cho các module nghiệp vụ:
- `GET /api/{module}`
- `POST /api/{module}`
- `GET /api/{module}/{id}`
- `PATCH /api/{module}/{id}`
- `DELETE /api/{module}/{id}`

Payload create/update: `{"data":{...}}`

Endpoint bổ sung:
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/me`
- `GET /api/dashboard`
- `GET /api/admin/audit`

## An toàn dữ liệu
V1 dùng database/storage riêng và không kết nối database QLDA cũ. Chỉ migration dữ liệu sau khi staging được kiểm thử và đối chiếu.

## Phạm vi V1 Foundation
Đã có end-to-end foundation cho đủ 12 module, data model lõi, API CRUD, auth, role foundation, audit trail, dashboard API, frontend navigation và Docker. Các tính năng chuyên sâu như approval nhiều cấp, Gantt tương tác, version file thực tế, thanh toán/procurement chi tiết, background notifications và AI provider là các increment tiếp theo trên cùng kiến trúc, không cần viết lại nền tảng.
