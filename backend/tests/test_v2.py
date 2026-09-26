from fastapi.testclient import TestClient
from app.v2 import app


def auth(client):
    r = client.post('/api/auth/login', json={'username':'admin','password':'TestPass123!'})
    assert r.status_code == 200
    return {'Authorization': f"Bearer {r.json()['access_token']}"}


def test_v2_end_to_end():
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        h = auth(client)
        p = client.post('/api/data/projects', headers=h, json={'code':'V2-P001','name':'V2 Project','status':'active','budget':1000000})
        assert p.status_code == 200
        pid = p.json()['id']

        task = client.post('/api/data/tasks', headers=h, json={'project_id':pid,'title':'Foundation','status':'in_progress','due_date':'2026-01-01','progress':25})
        assert task.status_code == 200
        task_id = task.json()['id']

        dep = client.post('/api/data/task-dependencies', headers=h, json={'project_id':pid,'task_id':task_id,'predecessor_id':task_id,'dependency_type':'FS','lag_days':0})
        assert dep.status_code == 200

        doc = client.post('/api/data/documents', headers=h, json={'project_id':pid,'document_no':'DOC-001','title':'Method Statement','status':'draft'})
        assert doc.status_code == 200
        tr = client.post('/api/workflow/transition', headers=h, json={'module':'documents','entity_id':doc.json()['id'],'to_status':'submitted','comment':'Submit for review'})
        assert tr.status_code == 200
        assert tr.json()['record']['status'] == 'submitted'

        contract = client.post('/api/data/contracts', headers=h, json={'project_id':pid,'contract_no':'HD-001','contractor':'ABC','contract_value':500000,'start_date':'2026-01-01','duration_days':30,'status':'draft'})
        assert contract.status_code == 200
        assert contract.json()['end_date'] == '2026-01-31'

        payment = client.post('/api/data/payments', headers=h, json={'project_id':pid,'contract_id':contract.json()['id'],'certificate_no':'IPC-01','gross_amount':100000,'net_amount':95000,'status':'draft'})
        assert payment.status_code == 200

        workload = client.get(f'/api/resources/workload?project_id={pid}', headers=h)
        assert workload.status_code == 200
        dashboard = client.get(f'/api/dashboard/summary?project_id={pid}', headers=h)
        assert dashboard.status_code == 200 and dashboard.json()['tasks']['total'] == 1
        risk = client.get(f'/api/ai/risk-summary?project_id={pid}', headers=h)
        assert risk.status_code == 200 and 'risk_score' in risk.json()
        search = client.get('/api/search?q=Foundation', headers=h)
        assert search.status_code == 200 and any(x['module']=='tasks' for x in search.json())
        export = client.get(f'/api/export/tasks.csv?project_id={pid}', headers=h)
        assert export.status_code == 200 and 'text/csv' in export.headers['content-type']
        audit = client.get('/api/data/audit-logs', headers=h)
        assert audit.status_code == 200 and len(audit.json()) >= 5
