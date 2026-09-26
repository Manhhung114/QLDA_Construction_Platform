import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import Base, engine, SessionLocal, get_db
from . import models
from .auth import hash_password, verify_password, create_token, current_user

app = FastAPI(title='QLDA Construction Platform API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

MODEL_MAP = {
 'projects': models.Project, 'wbs': models.WBSItem, 'tasks': models.Task,
 'schedule': models.ScheduleItem, 'resources': models.Resource, 'boq': models.BOQItem,
 'contracts': models.Contract, 'documents': models.Document, 'quality': models.QualityItem,
 'changes': models.ChangeRequest, 'collaboration': models.Comment, 'automation': models.WorkflowRule,
}

class LoginOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'
class RecordIn(BaseModel):
    data: dict[str, Any]
class RegisterIn(BaseModel):
    email: str
    full_name: str = ''
    password: str
    role: str = 'member'

def serialize(obj):
    result = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        if isinstance(value, (date, datetime)): value = value.isoformat()
        elif isinstance(value, Decimal): value = float(value)
        result[col.name] = value
    return result

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    if not email or not password:
        return
    db = SessionLocal()
    try:
        if not db.scalar(select(models.User).where(models.User.email == email)):
            db.add(models.User(email=email, full_name='System Admin', password_hash=hash_password(password), role='admin'))
            db.commit()
    finally:
        db.close()

@app.get('/health')
def health():
    return {'status':'ok','service':'qlda-api','version':'1.0.0'}

@app.post('/api/auth/login', response_model=LoginOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    return LoginOut(access_token=create_token(user))

@app.post('/api/auth/register')
def register(body: RegisterIn, db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role != 'admin': raise HTTPException(403, 'Admin only')
    if db.scalar(select(models.User).where(models.User.email == body.email)): raise HTTPException(409, 'Email exists')
    item = models.User(email=body.email, full_name=body.full_name, password_hash=hash_password(body.password), role=body.role)
    db.add(item); db.commit(); db.refresh(item)
    return serialize(item)

@app.get('/api/me')
def me(user=Depends(current_user)):
    return {'id':user.id,'email':user.email,'full_name':user.full_name,'role':user.role}

@app.get('/api/modules')
def modules_list():
    return [
      {'key':'projects','name':'Project & Portfolio'}, {'key':'tasks','name':'Task & WBS'},
      {'key':'schedule','name':'Schedule'}, {'key':'resources','name':'Resource'},
      {'key':'boq','name':'BOQ & Cost'}, {'key':'contracts','name':'Contract & Procurement'},
      {'key':'documents','name':'Document Control'}, {'key':'quality','name':'Quality'},
      {'key':'changes','name':'Change Management'}, {'key':'collaboration','name':'Collaboration'},
      {'key':'dashboard','name':'Dashboard & BI'}, {'key':'automation','name':'Automation & AI'}]

@app.get('/api/dashboard')
def dashboard(db: Session = Depends(get_db)):
    return {
      'projects': db.scalar(select(func.count(models.Project.id))) or 0,
      'tasks': db.scalar(select(func.count(models.Task.id))) or 0,
      'open_quality': db.scalar(select(func.count(models.QualityItem.id)).where(models.QualityItem.status != 'closed')) or 0,
      'documents': db.scalar(select(func.count(models.Document.id))) or 0,
      'changes': db.scalar(select(func.count(models.ChangeRequest.id))) or 0,
      'contract_value': float(db.scalar(select(func.coalesce(func.sum(models.Contract.value),0))) or 0),
      'boq_value': float(db.scalar(select(func.coalesce(func.sum(models.BOQItem.quantity * models.BOQItem.unit_price),0))) or 0)}

@app.get('/api/{module}')
def list_records(module: str, project_id: int | None = None, db: Session = Depends(get_db)):
    model = MODEL_MAP.get(module)
    if not model: raise HTTPException(404, 'Unknown module')
    stmt = select(model).order_by(model.id.desc()).limit(500)
    if project_id is not None and hasattr(model,'project_id'): stmt = stmt.where(model.project_id == project_id)
    return [serialize(x) for x in db.scalars(stmt).all()]

@app.get('/api/{module}/{record_id}')
def get_record(module: str, record_id: int, db: Session = Depends(get_db)):
    model = MODEL_MAP.get(module)
    if not model: raise HTTPException(404, 'Unknown module')
    item = db.get(model, record_id)
    if not item: raise HTTPException(404, 'Not found')
    return serialize(item)

@app.post('/api/{module}')
def create_record(module: str, body: RecordIn, db: Session = Depends(get_db), user=Depends(current_user)):
    model = MODEL_MAP.get(module)
    if not model: raise HTTPException(404, 'Unknown module')
    allowed = {c.name for c in model.__table__.columns if c.name not in {'id','created_at','updated_at'}}
    item = model(**{k:v for k,v in body.data.items() if k in allowed})
    db.add(item); db.flush()
    db.add(models.AuditLog(project_id=getattr(item,'project_id',None), actor_id=user.id, entity_type=module, entity_id=item.id, action='create', after_json=serialize(item)))
    db.commit(); db.refresh(item)
    return serialize(item)

@app.patch('/api/{module}/{record_id}')
def update_record(module: str, record_id: int, body: RecordIn, db: Session = Depends(get_db), user=Depends(current_user)):
    model = MODEL_MAP.get(module)
    if not model: raise HTTPException(404, 'Unknown module')
    item = db.get(model, record_id)
    if not item: raise HTTPException(404, 'Not found')
    before = serialize(item)
    allowed = {c.name for c in model.__table__.columns if c.name not in {'id','created_at','updated_at'}}
    for key,value in body.data.items():
        if key in allowed: setattr(item,key,value)
    db.add(models.AuditLog(project_id=getattr(item,'project_id',None), actor_id=user.id, entity_type=module, entity_id=item.id, action='update', before_json=before, after_json=serialize(item)))
    db.commit(); db.refresh(item)
    return serialize(item)

@app.delete('/api/{module}/{record_id}')
def delete_record(module: str, record_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role not in {'admin','manager'}: raise HTTPException(403, 'Insufficient permission')
    model = MODEL_MAP.get(module)
    if not model: raise HTTPException(404, 'Unknown module')
    item = db.get(model, record_id)
    if not item: raise HTTPException(404, 'Not found')
    before = serialize(item)
    db.add(models.AuditLog(project_id=getattr(item,'project_id',None), actor_id=user.id, entity_type=module, entity_id=item.id, action='delete', before_json=before))
    db.delete(item); db.commit()
    return {'deleted':True}

@app.get('/api/admin/audit')
def audit(db: Session = Depends(get_db), user=Depends(current_user)):
    if user.role not in {'admin','manager'}: raise HTTPException(403, 'Insufficient permission')
    return [serialize(x) for x in db.scalars(select(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(500)).all()]
