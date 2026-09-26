from fastapi.testclient import TestClient
from app.main import app


def test_core_12_module_foundation():
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200

        login = client.post('/api/auth/login', json={'username': 'admin', 'password': 'TestPass123!'})
        assert login.status_code == 200
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        project = client.post('/api/data/projects', headers=headers, json={
            'code': 'P001', 'name': 'Smoke Test Project', 'status': 'active', 'budget': 1000000
        })
        assert project.status_code == 200
        project_id = project.json()['id']

        task = client.post('/api/data/tasks', headers=headers, json={
            'project_id': project_id, 'title': 'Task A', 'status': 'in_progress',
            'due_date': '2026-01-01', 'progress': 30
        })
        assert task.status_code == 200

        contract = client.post('/api/data/contracts', headers=headers, json={
            'project_id': project_id, 'contract_no': 'HD001', 'contractor': 'ABC',
            'contract_value': 500000, 'start_date': '2026-01-01', 'duration_days': 30, 'status': 'active'
        })
        assert contract.status_code == 200
        assert contract.json()['end_date'] == '2026-01-31'

        quality = client.post('/api/data/quality', headers=headers, json={
            'project_id': project_id, 'item_type': 'NCR', 'number': 'NCR-01',
            'title': 'Test NCR', 'due_date': '2026-01-02', 'status': 'open'
        })
        assert quality.status_code == 200

        dashboard = client.get(f'/api/dashboard/summary?project_id={project_id}', headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()['tasks']['total'] == 1

        automation = client.post(f'/api/automation/run?project_id={project_id}', headers=headers)
        assert automation.status_code == 200
        assert automation.json()['alerts_detected'] >= 2

        risk = client.get(f'/api/ai/risk-summary?project_id={project_id}', headers=headers)
        assert risk.status_code == 200
        assert 'risk_score' in risk.json()

        upload = client.post('/api/files/upload', headers=headers, files={'file': ('hello.txt', b'hello', 'text/plain')})
        assert upload.status_code == 200
        assert upload.json()['url'].startswith('/uploads/')

        audit = client.get('/api/data/audit-logs', headers=headers)
        assert audit.status_code == 200
        assert len(audit.json()) >= 4
