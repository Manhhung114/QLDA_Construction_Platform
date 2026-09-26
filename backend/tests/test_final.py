import io

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.final import app


def auth(client):
    r=client.post('/api/auth/login',json={'username':'admin','password':'TestPass123!'})
    assert r.status_code==200
    return {'Authorization':f"Bearer {r.json()['access_token']}"}


def test_complete_beta_flow():
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        assert client.get('/ready').status_code==200
        h=auth(client)
        p=client.post('/api/data/projects',headers=h,json={'code':'FINAL-001','name':'Final Beta Project','status':'active','budget':2000000})
        assert p.status_code==200
        pid=p.json()['id']

        a=client.post('/api/data/schedule',headers=h,json={'project_id':pid,'activity_code':'A','name':'A','planned_start':'2026-01-01','planned_end':'2026-01-03','predecessor_ids':''})
        b=client.post('/api/data/schedule',headers=h,json={'project_id':pid,'activity_code':'B','name':'B','planned_start':'2026-01-04','planned_end':'2026-01-05','predecessor_ids':'A','milestone':False})
        assert a.status_code==200 and b.status_code==200
        cpm=client.get(f'/api/schedule/cpm?project_id={pid}',headers=h)
        assert cpm.status_code==200
        assert cpm.json()['duration_days']==5
        assert all('total_float_days' in row for row in cpm.json()['activities'])

        task=client.post('/api/data/tasks',headers=h,json={'project_id':pid,'title':'Install MEP','status':'in_progress','start_date':'2026-01-02','due_date':'2026-01-10'})
        assert task.status_code==200
        quality=client.post('/api/data/quality',headers=h,json={'project_id':pid,'item_type':'INS','number':'INS-01','title':'Inspection','status':'open','due_date':'2026-01-09'})
        assert quality.status_code==200
        cal=client.get(f'/api/calendar?project_id={pid}&start=2026-01-01&end=2026-01-31',headers=h)
        assert cal.status_code==200 and len(cal.json())>=3

        doc=client.post('/api/data/documents',headers=h,json={'project_id':pid,'document_no':'DOC-1','title':'Shop drawing','status':'draft'})
        assert doc.status_code==200
        tr=client.post('/api/workflow/transition',headers=h,json={'module':'documents','entity_id':doc.json()['id'],'to_status':'submitted','comment':'submit'})
        assert tr.status_code==200
        hist=client.get(f"/api/workflow/documents/{doc.json()['id']}/history",headers=h)
        assert hist.status_code==200 and len(hist.json())==1

        rule=client.post('/api/data/workflow-rules',headers=h,json={'project_id':pid,'module':'tasks','trigger_status':'in_progress','action_status':'review','enabled':True})
        assert rule.status_code==200
        run=client.post(f'/api/automation/rules/run?project_id={pid}',headers=h)
        assert run.status_code==200 and run.json()['changed']>=1
        task_after=client.get(f"/api/data/tasks/{task.json()['id']}",headers=h)
        assert task_after.json()['status']=='review'

        wb=Workbook(); ws=wb.active; ws.append(['item_code','description','unit','quantity','unit_rate','budget_amount']); ws.append(['B001','Cable','m',100,10,1000])
        buf=io.BytesIO(); wb.save(buf)
        imp=client.post(f'/api/import/boq?project_id={pid}',headers=h,files={'file':('boq.xlsx',buf.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
        assert imp.status_code==200 and imp.json()['created']==1

        export=client.get(f'/api/export/boq.csv?project_id={pid}',headers=h)
        assert export.status_code==200 and b'B001' in export.content
        dashboard=client.get(f'/api/dashboard/summary?project_id={pid}',headers=h)
        assert dashboard.status_code==200
        risk=client.get(f'/api/ai/risk-summary?project_id={pid}',headers=h)
        assert risk.status_code==200 and 'risk_level' in risk.json()
