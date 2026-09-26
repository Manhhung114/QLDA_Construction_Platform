# QLDA Construction Platform V2

Nền tảng quản lý dự án xây dựng mới, tách hoàn toàn khỏi QLDA cũ. V2 hướng tới **production beta**: 12 module dùng chung PostgreSQL, authentication, project RBAC, workflow phê duyệt, audit trail, file storage, dashboard, automation và các góc nhìn Kanban/Gantt/Calendar.

## 12 module

| # | Module | Phạm vi V2 |
|---|---|---|
| 1 | Project & Portfolio | Project, trạng thái, ngân sách, project members/roles, portfolio health |
| 2 | Task & WBS | WBS, task, priority, baseline, progress, checklist, FS/SS/FF/SF dependency, Kanban kéo-thả |
| 3 | Schedule | Planned/actual, milestone, predecessor, Gantt, CPM/critical path tính từ dependency |
| 4 | Resource & Time | Resource, capacity, assignment, allocation, timesheet, workload planned/actual |
| 5 | BOQ & Cost Control | BOQ, budget versions, actual/commitment/forecast, variance, Excel/CSV import-export |
| 6 | Contract & Procurement | Contract, tự tính end date, payment certificate, procurement, workflow |
| 7 | Document Control | Document, revision, file, transmittal, approve/reject/close history |
| 8 | Quality | RFI, NCR, INS, material, test, work inspection, deadline và workflow |
| 9 | Change Management | VO/change, cost/time impact, claim, workflow |
| 10 | Collaboration | Comment theo entity, notification, audit trail |
| 11 | Dashboard & BI | KPI, overdue, cost variance, portfolio health, CSV export, global search |
| 12 | Automation & AI | Workflow rules, overdue/contract alerts, saved rule engine, deterministic risk summary |

Các lớp nền tảng: User/Auth, JWT, project-level permission, immutable audit logs, upload hash SHA-256, extension allow-list, Alembic, health/readiness endpoints, Docker và CI.

## Góc nhìn trực quan

- **Kanban**: kéo thả task giữa `todo`, `in_progress`, `review`, `done`.
- **Gantt + CPM**: backend tính Early/Late Start/Finish, Total Float và Critical Path; frontend hiển thị timeline.
- **Calendar**: task start/deadline, milestone, quality due date, contract expiry, procurement expected date.
- **Portfolio**: health `green/amber/red` theo các chỉ số chậm tiến độ, quality và VO tồn.

## Workflow

Các nhóm hồ sơ có workflow kiểm soát, ví dụ:

```text
DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> CLOSED
                         |              ^
                         v              |
                      REJECTED -> SUBMITTED
```

Mỗi chuyển trạng thái được ghi `approval_actions` và `audit_logs`. Với module phải phê duyệt, không đổi trạng thái trực tiếp qua PATCH; phải gọi Workflow Transition.

## Import / Export

- Import `.csv` hoặc `.xlsx` cho các module nghiệp vụ chính.
- Header dùng field API; có thể **Export CSV** dữ liệu hiện hữu trước để làm template.
- Có `project_id` override khi import theo dự án.

## Chạy local / VPS bằng Docker

```bash
git clone https://github.com/Manhhung114/QLDA_Construction_Platform.git
cd QLDA_Construction_Platform
cp .env.example .env
# đổi POSTGRES_PASSWORD, JWT_SECRET, ADMIN_PASSWORD
docker compose up -d --build
```

Mặc định:

- Frontend: `127.0.0.1:3001`
- Backend: `127.0.0.1:8100`
- API health: `http://127.0.0.1:8100/health`
- Swagger: `http://127.0.0.1:8100/docs`

DB và uploads dùng volume riêng, không liên quan database QLDA cũ.

## API đáng chú ý

```text
POST /api/auth/login
GET  /api/auth/me
GET|POST /api/auth/users
GET|POST|PATCH|DELETE /api/data/{module}
POST /api/workflow/transition
GET  /api/workflow/{module}/{entity_id}/history
GET  /api/dashboard/summary
GET  /api/portfolio/summary
GET  /api/resources/workload
GET  /api/schedule/cpm
GET  /api/calendar
GET  /api/search
POST /api/import/{module}
GET  /api/export/{module}.csv
POST /api/automation/run
POST /api/automation/rules/run
GET  /api/ai/risk-summary
```

## Railway

Xem **[docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md)**. Mô hình đề xuất dùng một Railway Project với PostgreSQL + Backend + Frontend; Backend có persistent volume `/data` cho uploads và giao tiếp Frontend→Backend qua Railway private network.

## CI

GitHub Actions kiểm tra:

1. Backend end-to-end test trên SQLite.
2. Next.js production build.
3. Docker build cho backend và frontend.

Branch phát triển hiện tại: `v2-production-beta`. Chỉ merge vào `main` sau khi CI xanh.

## Production checklist

Trước khi dùng dữ liệu thật quy mô lớn:

- đổi toàn bộ secret/password mẫu;
- tạo Railway/VPS environment production riêng;
- bật backup PostgreSQL định kỳ;
- dùng persistent volume hoặc object storage cho files;
- cấu hình HTTPS/domain;
- kiểm tra RBAC bằng tài khoản contractor/reviewer/member;
- thiết lập monitoring/log retention;
- kiểm thử migration trên bản sao database trước nâng cấp lớn.
