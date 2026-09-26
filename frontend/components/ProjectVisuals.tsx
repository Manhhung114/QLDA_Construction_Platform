'use client';

import { useEffect, useMemo, useState } from 'react';
import styles from './ProjectVisuals.module.css';

const token = () => localStorage.getItem('qlda_token') || '';
const headers = () => ({'Content-Type':'application/json',Authorization:`Bearer ${token()}`});

export function KanbanBoard(){
  const [projectId,setProjectId]=useState(''); const [rows,setRows]=useState<any[]>([]); const [error,setError]=useState('');
  const columns=['todo','in_progress','review','done'];
  const load=async()=>{if(!projectId)return setError('Nhập Project ID.');const r=await fetch(`/api/data/tasks?project_id=${projectId}&limit=1000`,{headers:headers()});if(!r.ok)return setError(await r.text());setRows(await r.json());setError('');};
  const move=async(id:number,status:string)=>{const r=await fetch(`/api/data/tasks/${id}`,{method:'PATCH',headers:headers(),body:JSON.stringify({status})});if(!r.ok)return setError(await r.text());await load();};
  return <section className={styles.panel}><div className={styles.toolbar}><h3>Kanban Board</h3><input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/><button onClick={load}>Tải Kanban</button></div>{error&&<p className={styles.error}>{error}</p>}<div className={styles.kanban}>{columns.map(col=><div key={col} className={styles.kanbanColumn} onDragOver={e=>e.preventDefault()} onDrop={e=>{const id=Number(e.dataTransfer.getData('text/plain'));if(id)move(id,col);}}><h4>{col.replace('_',' ')}</h4>{rows.filter(r=>r.status===col).map(r=><article draggable onDragStart={e=>e.dataTransfer.setData('text/plain',String(r.id))} key={r.id} className={styles.card}><b>#{r.id} {r.title}</b><small>{r.assignee||'Chưa gán'} · {r.progress||0}%</small><small>Deadline: {r.due_date||'—'} · {r.priority||'medium'}</small></article>)}</div>)}</div></section>;
}

export function GanttCPM(){
  const [projectId,setProjectId]=useState(''); const [data,setData]=useState<any>(null); const [error,setError]=useState('');
  const load=async()=>{if(!projectId)return setError('Nhập Project ID.');const r=await fetch(`/api/schedule/cpm?project_id=${projectId}`,{headers:headers()});if(!r.ok)return setError(await r.text());setData(await r.json());setError('');};
  const duration=Math.max(1,data?.duration_days||1);
  return <section className={styles.panel}><div className={styles.toolbar}><h3>Gantt & Critical Path</h3><input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/><button onClick={load}>Tính CPM</button></div>{error&&<p className={styles.error}>{error}</p>}{data&&<><p>Tổng thời lượng CPM: <b>{data.duration_days} ngày</b>. Thanh có nhãn <b>Critical</b> có total float = 0.</p><div className={styles.gantt}>{data.activities.map((a:any)=><div className={styles.ganttRow} key={a.id}><div className={styles.ganttLabel}><b>{a.activity_code}</b><span>{a.name}</span></div><div className={styles.track}><div className={`${styles.bar} ${a.computed_critical?styles.critical:''}`} style={{left:`${(a.early_start_day/duration)*100}%`,width:`${Math.max(2,(a.duration_days/duration)*100)}%`}} title={`ES ${a.early_start_day}; EF ${a.early_finish_day}; Float ${a.total_float_days}`}><small>{a.duration_days}d {a.computed_critical?'· Critical':''}</small></div></div></div>)}</div></>}</section>;
}

export function ProjectCalendar(){
  const [projectId,setProjectId]=useState(''); const now=new Date(); const [month,setMonth]=useState(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`); const [events,setEvents]=useState<any[]>([]); const [error,setError]=useState('');
  const [year,mon]=month.split('-').map(Number); const first=new Date(year,mon-1,1); const last=new Date(year,mon,0); const start=`${month}-01`; const end=`${month}-${String(last.getDate()).padStart(2,'0')}`;
  const load=async()=>{if(!projectId)return setError('Nhập Project ID.');const r=await fetch(`/api/calendar?project_id=${projectId}&start=${start}&end=${end}`,{headers:headers()});if(!r.ok)return setError(await r.text());setEvents(await r.json());setError('');};
  const cells=useMemo(()=>{const items:Array<number|null>=[];for(let i=0;i<first.getDay();i++)items.push(null);for(let d=1;d<=last.getDate();d++)items.push(d);return items;},[month]);
  return <section className={styles.panel}><div className={styles.toolbar}><h3>Calendar</h3><input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/><input type="month" value={month} onChange={e=>setMonth(e.target.value)}/><button onClick={load}>Tải lịch</button></div>{error&&<p className={styles.error}>{error}</p>}<div className={styles.calendar}>{['CN','T2','T3','T4','T5','T6','T7'].map(x=><b key={x} className={styles.dayHead}>{x}</b>)}{cells.map((d,i)=><div key={i} className={styles.day}>{d&&<><strong>{d}</strong>{events.filter(e=>Number(e.date.slice(8,10))===d).map((e:any,j:number)=><small key={`${e.type}-${e.id}-${j}`} title={e.title}>{e.title}</small>)}</>}</div>)}</div></section>;
}

export function ImportPanel({module,projectScoped}:{module:string;projectScoped?:boolean}){
  const [projectId,setProjectId]=useState(''); const [file,setFile]=useState<File|null>(null); const [result,setResult]=useState<any>(null); const [error,setError]=useState('');
  const upload=async()=>{if(!file)return setError('Chọn file CSV/XLSX.');if(projectScoped&&!projectId)return setError('Nhập Project ID.');const body=new FormData();body.append('file',file);const qs=projectId?`?project_id=${projectId}`:'';const r=await fetch(`/api/import/${module}${qs}`,{method:'POST',headers:{Authorization:`Bearer ${token()}`},body});if(!r.ok)return setError(await r.text());setResult(await r.json());setError('');};
  return <section className={styles.panel}><div className={styles.toolbar}><h3>Import CSV/XLSX</h3>{projectScoped&&<input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/>}<input type="file" accept=".csv,.xlsx" onChange={e=>setFile(e.target.files?.[0]||null)}/><button onClick={upload}>Import</button></div><p>Hàng tiêu đề phải dùng đúng tên field API của module. Có thể tải dữ liệu hiện hữu bằng nút “Xuất CSV” để dùng làm mẫu.</p>{error&&<p className={styles.error}>{error}</p>}{result&&<pre className={styles.result}>{JSON.stringify(result,null,2)}</pre>}</section>;
}
