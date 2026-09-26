'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import type { FieldDef, ModuleDef } from '@/lib/modules';

const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('qlda_token') || ''}`
});

function formatValue(value: unknown) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? '✓' : '—';
  if (typeof value === 'number') return new Intl.NumberFormat('vi-VN').format(value);
  return String(value);
}

function DashboardPanel() {
  const [projectId, setProjectId] = useState('');
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    const qs = projectId ? `?project_id=${projectId}` : '';
    const res = await fetch(`/api/dashboard/summary${qs}`, { headers: authHeaders() });
    if (!res.ok) return setError(await res.text());
    setData(await res.json());
  };

  useEffect(() => { load(); }, []);

  return <div className="workspace">
    <div className="toolbar"><input placeholder="Project ID (để trống = toàn bộ)" value={projectId} onChange={e=>setProjectId(e.target.value)} /><button onClick={load}>Cập nhật</button></div>
    {error && <p className="error">{error}</p>}
    {data && <>
      <div className="kpi-grid">
        <div className="kpi"><span>Dự án</span><strong>{data.projects}</strong></div>
        <div className="kpi"><span>Task</span><strong>{data.tasks.total}</strong><small>{data.tasks.overdue} quá hạn</small></div>
        <div className="kpi"><span>Hồ sơ chờ</span><strong>{data.documents_pending}</strong></div>
        <div className="kpi"><span>Quality mở</span><strong>{data.quality_open}</strong></div>
        <div className="kpi"><span>VO chờ</span><strong>{data.changes_pending}</strong></div>
        <div className="kpi"><span>Giá trị HĐ</span><strong>{formatValue(data.contract_value)}</strong></div>
      </div>
      <div className="panel"><h3>Chi phí</h3><div className="cost-row"><span>Budget: <b>{formatValue(data.cost.budget)}</b></span><span>Actual: <b>{formatValue(data.cost.actual)}</b></span><span>Variance: <b>{formatValue(data.cost.variance)}</b></span></div></div>
    </>}
  </div>;
}

export default function ModuleWorkspace({ module }: { module: ModuleDef }) {
  const [activeEndpoint, setActiveEndpoint] = useState(module.endpoint || '');
  const [fields, setFields] = useState<FieldDef[]>(module.fields || []);
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState<Record<string, any>>({});
  const [editingId, setEditingId] = useState<number | null>(null);
  const [projectId, setProjectId] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [specialResult, setSpecialResult] = useState<any>(null);

  if (module.special === 'dashboard') return <DashboardPanel />;

  const columns = useMemo(() => {
    const keys = ['id', ...fields.map(f => f.key), 'created_at'];
    return Array.from(new Set(keys));
  }, [fields]);

  const load = async () => {
    if (!activeEndpoint) return;
    setError('');
    const qs = module.projectScoped && projectId ? `?project_id=${projectId}` : '';
    const res = await fetch(`/api/data/${activeEndpoint}${qs}`, { headers: authHeaders() });
    if (res.status === 401) return setError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
    if (!res.ok) return setError(await res.text());
    setRows(await res.json());
  };

  useEffect(() => { load(); }, [activeEndpoint]);

  const switchEndpoint = (endpoint: string, nextFields: FieldDef[]) => {
    setActiveEndpoint(endpoint); setFields(nextFields); setForm({}); setEditingId(null); setShowForm(false); setRows([]);
  };

  const upload = async (file: File, key: string) => {
    const body = new FormData(); body.append('file', file);
    const res = await fetch('/api/files/upload', { method:'POST', headers:{ Authorization:`Bearer ${localStorage.getItem('qlda_token') || ''}` }, body });
    if (!res.ok) return setError(await res.text());
    const data = await res.json(); setForm(prev => ({...prev, [key]: data.url}));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    const url = editingId ? `/api/data/${activeEndpoint}/${editingId}` : `/api/data/${activeEndpoint}`;
    const res = await fetch(url, { method: editingId ? 'PATCH' : 'POST', headers: authHeaders(), body: JSON.stringify(form) });
    setBusy(false);
    if (!res.ok) return setError(await res.text());
    setForm({}); setEditingId(null); setShowForm(false); await load();
  };

  const edit = (row: any) => {
    const values: Record<string, any> = {};
    fields.forEach(f => values[f.key] = row[f.key] ?? '');
    setForm(values); setEditingId(row.id); setShowForm(true);
  };

  const remove = async (id: number) => {
    if (!confirm('Xóa bản ghi này?')) return;
    const res = await fetch(`/api/data/${activeEndpoint}/${id}`, { method:'DELETE', headers:authHeaders() });
    if (!res.ok) return setError(await res.text());
    await load();
  };

  const runAutomation = async () => {
    const qs = projectId ? `?project_id=${projectId}` : '';
    const res = await fetch(`/api/automation/run${qs}`, { method:'POST', headers:authHeaders() });
    setSpecialResult(await res.json());
  };

  const runRisk = async () => {
    if (!projectId) return setError('Nhập Project ID để phân tích rủi ro.');
    const res = await fetch(`/api/ai/risk-summary?project_id=${projectId}`, { headers:authHeaders() });
    setSpecialResult(await res.json());
  };

  return <div className="workspace">
    <div className="toolbar wrap">
      <Link className="link-button ghost-link" href="/">← Tổng quan</Link>
      {module.projectScoped && <input placeholder="Lọc Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)} />}
      <button onClick={load}>Lọc / Làm mới</button>
      {activeEndpoint && <button onClick={()=>{setShowForm(!showForm);setEditingId(null);setForm({});}}>+ Thêm mới</button>}
      {module.special === 'automation' && <><button onClick={runAutomation}>Chạy cảnh báo</button><button onClick={runRisk}>AI Risk Summary</button></>}
    </div>

    {(module.secondary?.length || 0) > 0 && <div className="tabs">
      <button className={activeEndpoint===module.endpoint?'active':''} onClick={()=>switchEndpoint(module.endpoint || '', module.fields || [])}>{module.title}</button>
      {module.secondary?.map(s=><button key={s.endpoint} className={activeEndpoint===s.endpoint?'active':''} onClick={()=>switchEndpoint(s.endpoint,s.fields)}>{s.label}</button>)}
    </div>}

    {specialResult && <pre className="result-box">{JSON.stringify(specialResult,null,2)}</pre>}
    {error && <p className="error">{error}</p>}

    {showForm && <form className="panel form-grid" onSubmit={submit}>
      <h3>{editingId ? `Sửa #${editingId}` : 'Thêm bản ghi'}</h3>
      {fields.map(field => <label key={field.key} className={field.type==='textarea'?'wide':''}>
        <span>{field.label}{field.required?' *':''}</span>
        {field.type === 'textarea' ? <textarea required={field.required} value={form[field.key] ?? ''} onChange={e=>setForm({...form,[field.key]:e.target.value})} />
        : field.type === 'select' ? <select required={field.required} value={form[field.key] ?? ''} onChange={e=>setForm({...form,[field.key]:e.target.value})}><option value="">-- chọn --</option>{field.options?.map(o=><option key={o}>{o}</option>)}</select>
        : field.type === 'checkbox' ? <input type="checkbox" checked={Boolean(form[field.key])} onChange={e=>setForm({...form,[field.key]:e.target.checked})} />
        : field.type === 'file' ? <><input type="file" onChange={e=>e.target.files?.[0] && upload(e.target.files[0],field.key)} /><small>{form[field.key] || 'Chưa có file'}</small></>
        : <input required={field.required} type={field.type || 'text'} step={field.type==='number'?'any':undefined} value={form[field.key] ?? ''} onChange={e=>setForm({...form,[field.key]:e.target.value})} />}
      </label>)}
      <div className="wide form-actions"><button disabled={busy}>{busy?'Đang lưu...':'Lưu'}</button><button type="button" className="ghost" onClick={()=>setShowForm(false)}>Hủy</button></div>
    </form>}

    <div className="table-wrap">
      <table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}<th>Thao tác</th></tr></thead>
      <tbody>{rows.map(row=><tr key={row.id}>{columns.map(c=><td key={c}>{formatValue(row[c])}</td>)}<td className="actions"><button onClick={()=>edit(row)}>Sửa</button><button className="danger" onClick={()=>remove(row.id)}>Xóa</button></td></tr>)}</tbody></table>
      {!rows.length && <div className="empty">Chưa có dữ liệu.</div>}
    </div>
  </div>;
}
