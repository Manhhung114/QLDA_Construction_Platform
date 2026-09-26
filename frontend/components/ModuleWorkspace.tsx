'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import type { FieldDef, ModuleDef } from '@/lib/modules';
import { displayLabel } from '@/lib/productionProfile';

const authHeaders = () => ({ 'Content-Type':'application/json', Authorization:`Bearer ${localStorage.getItem('qlda_token') || ''}` });
const approvable = new Set(['documents','document-revisions','quality','changes','claims','contracts','payments','procurement','budget-versions']);
const nested = new Set(['project-members','checklists','document-revisions']);
const workflow: Record<string, Record<string,string[]>> = {
  documents:{draft:['submitted'],submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted'],approved:['closed']},
  'document-revisions':{submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted']},
  quality:{open:['submitted','closed'],submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted'],approved:['closed']},
  changes:{draft:['submitted'],submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted'],approved:['closed']},
  claims:{draft:['submitted'],submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted'],approved:['closed']},
  contracts:{draft:['active','cancelled'],active:['expired','closed','cancelled']},
  payments:{draft:['submitted'],submitted:['under_review','rejected'],under_review:['approved','rejected'],rejected:['submitted'],approved:['paid']},
  procurement:{requested:['approved','cancelled'],approved:['ordered'],ordered:['delivered','cancelled'],delivered:['closed']},
  'budget-versions':{draft:['submitted'],submitted:['approved','rejected'],rejected:['draft']}
};

const systemLabels: Record<string,string> = {
  id:'ID', created_at:'Ngày tạo', updated_at:'Cập nhật', project_id:'Project ID', status:'Trạng thái',
  title:'Tiêu đề', description:'Mô tả', note:'Ghi chú', progress:'Tiến độ %'
};

function formatDateLike(value:string) {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/);
  if (!match) return value;
  const [,y,m,d,hh,mm] = match;
  return hh ? `${d}/${m}/${y} ${hh}:${mm}` : `${d}/${m}/${y}`;
}

function formatValue(value: unknown, field?: FieldDef) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? '✓' : '—';
  if (typeof value === 'number') return new Intl.NumberFormat('vi-VN').format(value);
  const text = String(value);
  if (field?.type === 'select') return displayLabel(text, field.optionLabels);
  if (field?.type === 'date' || /^\d{4}-\d{2}-\d{2}/.test(text)) return formatDateLike(text);
  return displayLabel(text, field?.optionLabels);
}

function DashboardPanel() {
  const [projectId,setProjectId] = useState('');
  const [data,setData] = useState<any>(null);
  const [portfolio,setPortfolio] = useState<any[]>([]);
  const [error,setError] = useState('');
  const load = async () => {
    setError(''); const qs = projectId ? `?project_id=${projectId}` : '';
    const [r,p] = await Promise.all([fetch(`/api/dashboard/summary${qs}`,{headers:authHeaders()}), fetch('/api/portfolio/summary',{headers:authHeaders()})]);
    if (!r.ok) return setError(await r.text()); setData(await r.json()); if (p.ok) setPortfolio(await p.json());
  };
  useEffect(()=>{load();},[]);
  return <div className="workspace">
    <div className="toolbar"><input placeholder="Project ID (trống = toàn bộ)" value={projectId} onChange={e=>setProjectId(e.target.value)} /><button onClick={load}>Cập nhật</button></div>
    {error&&<p className="error">{error}</p>}
    {data&&<><div className="kpi-grid">
      <div className="kpi"><span>Dự án</span><strong>{data.projects}</strong></div><div className="kpi"><span>Công việc</span><strong>{data.tasks.total}</strong><small>{data.tasks.overdue} quá hạn · {data.tasks.completion_percent}% hoàn thành</small></div>
      <div className="kpi"><span>Hồ sơ chờ</span><strong>{data.documents_pending}</strong></div><div className="kpi"><span>Chất lượng mở</span><strong>{data.quality_open}</strong></div>
      <div className="kpi"><span>VO chờ</span><strong>{data.changes_pending}</strong></div><div className="kpi"><span>Giá trị HĐ</span><strong>{formatValue(data.contract_value)}</strong></div>
    </div><div className="panel"><h3>Chi phí</h3><div className="cost-row"><span>Ngân sách: <b>{formatValue(data.cost.budget)}</b></span><span>Thực tế: <b>{formatValue(data.cost.actual)}</b></span><span>Chênh lệch: <b>{formatValue(data.cost.variance)}</b></span></div></div></>}
    {!!portfolio.length&&<div className="panel"><h3>Sức khỏe Portfolio</h3><div className="table-wrap"><table><thead><tr><th>Mã</th><th>Dự án</th><th>Health</th><th>Task quá hạn</th><th>Quality mở</th><th>VO chờ</th></tr></thead><tbody>{portfolio.map(p=><tr key={p.id}><td>{p.code}</td><td>{p.name}</td><td><b>{p.health}</b></td><td>{p.metrics.tasks.overdue}</td><td>{p.metrics.quality_open}</td><td>{p.metrics.changes_pending}</td></tr>)}</tbody></table></div></div>}
  </div>;
}

export default function ModuleWorkspace({module}:{module:ModuleDef}) {
  const [activeEndpoint,setActiveEndpoint] = useState(module.endpoint || '');
  const [fields,setFields] = useState<FieldDef[]>(module.fields || []);
  const [rows,setRows] = useState<any[]>([]);
  const [form,setForm] = useState<Record<string,any>>({});
  const [editingId,setEditingId] = useState<number|null>(null);
  const [projectId,setProjectId] = useState('');
  const [query,setQuery] = useState('');
  const [showForm,setShowForm] = useState(false);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [specialResult,setSpecialResult] = useState<any>(null);

  if (module.special==='dashboard') return <DashboardPanel/>;
  const readOnly = ['audit-logs','approval-actions'].includes(activeEndpoint);
  const isNested = nested.has(activeEndpoint);
  const needsProject = module.projectScoped || isNested;
  const columns = useMemo(()=>Array.from(new Set(['id',...fields.map(f=>f.key),'created_at'])),[fields]);
  const fieldByKey = useMemo(()=>Object.fromEntries(fields.map(f=>[f.key,f])),[fields]);

  const load = async () => {
    if (!activeEndpoint) return;
    if (isNested && !projectId) return setError('Nhập Project ID để tải dữ liệu thuộc dự án.');
    setError(''); const params = new URLSearchParams();
    if (projectId) params.set('project_id',projectId); if (query && !isNested) params.set('q',query);
    const base = isNested ? `/api/scoped/${activeEndpoint}` : `/api/data/${activeEndpoint}`;
    const res = await fetch(`${base}?${params}`,{headers:authHeaders()});
    if (res.status===401) return setError('Phiên đăng nhập đã hết hạn.'); if (!res.ok) return setError(await res.text()); setRows(await res.json());
  };
  useEffect(()=>{ if(!isNested) load(); },[activeEndpoint]);

  const switchEndpoint = (endpoint:string,nextFields:FieldDef[]) => { setActiveEndpoint(endpoint); setFields(nextFields); setForm({}); setEditingId(null); setShowForm(false); setRows([]); setSpecialResult(null); };
  const upload = async (file:File,key:string) => { const body=new FormData(); body.append('file',file); const res=await fetch('/api/files/upload',{method:'POST',headers:{Authorization:`Bearer ${localStorage.getItem('qlda_token') || ''}`},body}); if(!res.ok)return setError(await res.text()); const data=await res.json(); setForm(prev=>({...prev,[key]:data.url})); };
  const submit = async (e:React.FormEvent) => { e.preventDefault(); setBusy(true); setError(''); const payload={...form}; if(projectId && fields.some(f=>f.key==='project_id') && !payload.project_id) payload.project_id=projectId; const url=editingId?`/api/data/${activeEndpoint}/${editingId}`:`/api/data/${activeEndpoint}`; const res=await fetch(url,{method:editingId?'PATCH':'POST',headers:authHeaders(),body:JSON.stringify(payload)}); setBusy(false); if(!res.ok)return setError(await res.text()); setForm({});setEditingId(null);setShowForm(false);await load(); };
  const edit = (row:any) => { const values:Record<string,any>={}; fields.forEach(f=>values[f.key]=row[f.key]??''); setForm(values);setEditingId(row.id);setShowForm(true); };
  const remove = async (id:number) => { if(!confirm('Xóa bản ghi này?'))return; const res=await fetch(`/api/data/${activeEndpoint}/${id}`,{method:'DELETE',headers:authHeaders()}); if(!res.ok)return setError(await res.text());await load(); };
  const transition = async (row:any,target:string) => { const comment=prompt(`Ghi chú chuyển ${displayLabel(row.status)} → ${displayLabel(target)}`) || ''; const res=await fetch('/api/workflow/transition',{method:'POST',headers:authHeaders(),body:JSON.stringify({module:activeEndpoint,entity_id:row.id,to_status:target,comment})}); if(!res.ok)return setError(await res.text());await load(); };
  const exportCsv = async () => { if(isNested)return setError('Dữ liệu con được bảo vệ theo Project ID; export dùng ở module chính.'); const qs=projectId?`?project_id=${projectId}`:''; const res=await fetch(`/api/export/${activeEndpoint}.csv${qs}`,{headers:authHeaders()}); if(!res.ok)return setError(await res.text()); const blob=await res.blob(); const url=URL.createObjectURL(blob); const a=document.createElement('a');a.href=url;a.download=`${activeEndpoint}.csv`;a.click();URL.revokeObjectURL(url); };
  const runAutomation = async () => { const qs=projectId?`?project_id=${projectId}`:'';const res=await fetch(`/api/automation/run${qs}`,{method:'POST',headers:authHeaders()});setSpecialResult(await res.json()); };
  const runRisk = async () => { if(!projectId)return setError('Nhập Project ID để phân tích rủi ro.');const res=await fetch(`/api/ai/risk-summary?project_id=${projectId}`,{headers:authHeaders()});setSpecialResult(await res.json()); };
  const runWorkload = async () => { if(!projectId)return setError('Nhập Project ID để xem workload.');const res=await fetch(`/api/resources/workload?project_id=${projectId}`,{headers:authHeaders()});setSpecialResult(await res.json()); };

  return <div className="workspace">
    <div className="toolbar wrap sticky-toolbar">
      <Link className="link-button ghost-link" href="/">← Tổng quan</Link>
      {needsProject&&<input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/>}<input placeholder="Tìm trong module" value={query} onChange={e=>setQuery(e.target.value)} disabled={isNested}/>
      <button onClick={load}>Tìm / Làm mới</button>{!isNested&&<button className="ghost" onClick={exportCsv}>Xuất CSV</button>}
      {!readOnly&&activeEndpoint&&<button onClick={()=>{setShowForm(!showForm);setEditingId(null);setForm({});}}>+ Thêm mới</button>}
      {module.slug==='resources'&&<button className="ghost" onClick={runWorkload}>Workload</button>}
      {module.special==='automation'&&<><button onClick={runAutomation}>Chạy cảnh báo</button><button className="ghost" onClick={runRisk}>Risk Summary</button></>}
    </div>
    {(module.secondary?.length||0)>0&&<div className="tabs"><button className={activeEndpoint===module.endpoint?'active':''} onClick={()=>switchEndpoint(module.endpoint||'',module.fields||[])}>{module.title}</button>{module.secondary?.map(s=><button key={s.endpoint} className={activeEndpoint===s.endpoint?'active':''} onClick={()=>switchEndpoint(s.endpoint,s.fields)}>{s.label}</button>)}</div>}
    {specialResult&&<pre className="result-box">{JSON.stringify(specialResult,null,2)}</pre>}{error&&<p className="error">{error}</p>}
    {showForm&&!readOnly&&<form className="panel form-grid" onSubmit={submit}><h3>{editingId?`Sửa #${editingId}`:'Thêm bản ghi'}</h3>{fields.map(field=><label key={field.key} className={field.type==='textarea'?'wide':''}><span>{field.label}{field.required?' *':''}</span>{field.type==='textarea'?<textarea required={field.required} value={form[field.key]??''} onChange={e=>setForm({...form,[field.key]:e.target.value})}/>:field.type==='select'?<select required={field.required} value={form[field.key]??''} onChange={e=>setForm({...form,[field.key]:e.target.value})}><option value="">-- chọn --</option>{field.options?.map(o=><option key={o} value={o}>{displayLabel(o,field.optionLabels)}</option>)}</select>:field.type==='checkbox'?<input type="checkbox" checked={Boolean(form[field.key])} onChange={e=>setForm({...form,[field.key]:e.target.checked})}/>:field.type==='file'?<><input type="file" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0],field.key)}/><small>{form[field.key]||'Chưa có file'}</small></>:<input required={field.required} type={field.type||'text'} step={field.type==='number'?'any':undefined} value={form[field.key]??''} onChange={e=>setForm({...form,[field.key]:e.target.value})}/>}</label>)}<div className="wide form-actions"><button disabled={busy}>{busy?'Đang lưu...':'Lưu'}</button><button type="button" className="ghost" onClick={()=>setShowForm(false)}>Hủy</button></div></form>}
    <div className="table-wrap"><table><thead><tr>{columns.map(c=><th key={c}>{fieldByKey[c]?.label||systemLabels[c]||c}</th>)}<th>Thao tác</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}>{columns.map(c=><td key={c}>{formatValue(row[c],fieldByKey[c])}</td>)}<td className="actions">{!readOnly&&<><button onClick={()=>edit(row)}>Sửa</button><button className="danger" onClick={()=>remove(row.id)}>Xóa</button></>}{approvable.has(activeEndpoint)&&row.status&&workflow[activeEndpoint]?.[row.status]?.map(target=><button className="workflow-action" key={target} onClick={()=>transition(row,target)}>{displayLabel(target)}</button>)}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty">Chưa có dữ liệu.</div>}</div>
  </div>;
}
