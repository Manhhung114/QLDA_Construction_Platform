'use client';
import {useEffect,useMemo,useState} from 'react';
import Link from 'next/link';
import {modules} from '@/lib/modules';
import {fields} from '@/lib/fields';
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8100';

type Row=Record<string,unknown>;
export default function ModuleWorkspace({slug}:{slug:string}){
 const module=modules.find(x=>x.slug===slug); const moduleFields=fields[slug]||[];
 const [rows,setRows]=useState<Row[]>([]); const [form,setForm]=useState<Record<string,string>>({}); const [error,setError]=useState(''); const [loading,setLoading]=useState(true);
 const token=typeof window!=='undefined'?localStorage.getItem('qlda_token'):null;
 const headers=useMemo(()=>token?{'Authorization':`Bearer ${token}`}:{} as Record<string,string>,[token]);
 async function load(){setLoading(true);setError('');try{if(slug==='dashboard'){const r=await fetch(`${API}/api/dashboard`);if(!r.ok)throw new Error(await r.text());setRows([await r.json()]);}else{const r=await fetch(`${API}/api/${slug}`);if(!r.ok)throw new Error(await r.text());setRows(await r.json());}}catch(e){setError(String(e));}finally{setLoading(false)}}
 useEffect(()=>{load()},[slug]);
 async function create(){if(!token){setError('Cần đăng nhập để tạo dữ liệu.');return}const data:Record<string,unknown>={};for(const f of moduleFields){const v=form[f.key];if(v===undefined||v==='')continue;data[f.key]=f.type==='number'?Number(v):v;}const r=await fetch(`${API}/api/${slug}`,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify({data})});if(!r.ok){setError(await r.text());return}setForm({});await load()}
 async function remove(id:unknown){if(!token){setError('Cần đăng nhập.');return}if(!confirm('Xóa bản ghi này?'))return;const r=await fetch(`${API}/api/${slug}/${id}`,{method:'DELETE',headers});if(!r.ok){setError(await r.text());return}await load()}
 if(!module)return <section><h1>Không tìm thấy module</h1></section>;
 const cols=rows[0]?Object.keys(rows[0]).filter(x=>!['created_at','updated_at'].includes(x)).slice(0,9):[];
 return <section><div className="moduleHead"><div><p className="eyebrow">MODULE</p><h1>{module.icon} {module.name}</h1><p>{module.desc}</p></div><div className="actions"><Link className="ghost" href="/login">Đăng nhập</Link><Link className="button" href="/">← Tổng quan</Link></div></div>
 {error&&<div className="error">{error}</div>}
 {slug!=='dashboard'&&moduleFields.length>0&&<div className="panel"><h2>Tạo bản ghi</h2><div className="formGrid">{moduleFields.map(f=><label key={f.key}><span>{f.label}</span>{f.type==='select'?<select value={form[f.key]||''} onChange={e=>setForm({...form,[f.key]:e.target.value})}><option value="">-- chọn --</option>{f.options?.map(o=><option key={o}>{o}</option>)}</select>:<input type={f.type||'text'} value={form[f.key]||''} onChange={e=>setForm({...form,[f.key]:e.target.value})}/>}</label>)}</div><button className="primary" onClick={create}>+ Thêm</button></div>}
 <div className="panel"><div className="tableTitle"><h2>Dữ liệu</h2><button className="ghostBtn" onClick={load}>Làm mới</button></div>{loading?<p>Đang tải...</p>:rows.length===0?<p className="muted">Chưa có dữ liệu.</p>:<div className="tableWrap"><table><thead><tr>{cols.map(c=><th key={c}>{c}</th>)}{slug!=='dashboard'&&<th></th>}</tr></thead><tbody>{rows.map((r,i)=><tr key={String(r.id??i)}>{cols.map(c=><td key={c}>{typeof r[c]==='object'?JSON.stringify(r[c]):String(r[c]??'')}</td>)}{slug!=='dashboard'&&<td><button className="danger" onClick={()=>remove(r.id)}>Xóa</button></td>}</tr>)}</tbody></table></div>}</div></section>
}
