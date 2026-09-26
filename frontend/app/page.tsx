'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { modules } from '@/lib/modules';
import { businessGroups } from '@/lib/productionProfile';

const authHeaders = (token:string) => ({Authorization:`Bearer ${token}`});
const money = (value:unknown) => new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(Number(value||0));

export default function Home(){
  const [token,setToken]=useState('');
  const [username,setUsername]=useState('admin');
  const [password,setPassword]=useState('');
  const [user,setUser]=useState<any>(null);
  const [error,setError]=useState('');
  const [q,setQ]=useState('');
  const [results,setResults]=useState<any[]>([]);
  const [summary,setSummary]=useState<any>(null);

  const moduleMap=useMemo(()=>Object.fromEntries(modules.map(m=>[m.slug,m])),[]);

  const loadSession=async(saved:string)=>{
    const [me,dash]=await Promise.all([
      fetch('/api/auth/me',{headers:authHeaders(saved)}),
      fetch('/api/dashboard/summary',{headers:authHeaders(saved)})
    ]);
    if(me.ok)setUser(await me.json());
    if(dash.ok)setSummary(await dash.json());
  };

  useEffect(()=>{
    const saved=localStorage.getItem('qlda_token')||'';
    setToken(saved);
    if(saved)loadSession(saved);
  },[]);

  const login=async(e:React.FormEvent)=>{
    e.preventDefault();setError('');
    const res=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
    if(!res.ok)return setError('Không đăng nhập được. Kiểm tra tài khoản/mật khẩu.');
    const data=await res.json();
    localStorage.setItem('qlda_token',data.access_token);
    setToken(data.access_token);setUser(data.user);setPassword('');
    const dash=await fetch('/api/dashboard/summary',{headers:authHeaders(data.access_token)});
    if(dash.ok)setSummary(await dash.json());
  };

  const logout=()=>{localStorage.removeItem('qlda_token');setToken('');setUser(null);setResults([]);setSummary(null);};
  const search=async(e:React.FormEvent)=>{e.preventDefault();if(q.trim().length<2)return;const r=await fetch(`/api/search?q=${encodeURIComponent(q)}`,{headers:authHeaders(localStorage.getItem('qlda_token')||'')});if(r.ok)setResults(await r.json());};

  if(!token)return <main className="login-page"><form className="login-card" onSubmit={login}><div className="brand-mark">QLDA</div><p className="eyebrow">Construction Project Management</p><h1>QLDA Xây dựng</h1><p>Nền tảng điều hành dự án, hồ sơ, tiến độ, chi phí và chất lượng.</p><label>Tài khoản<input value={username} onChange={e=>setUsername(e.target.value)}/></label><label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)}/></label>{error&&<p className="error">{error}</p>}<button>Đăng nhập</button></form></main>;

  return <main className="shell production-shell">
    <header className="topbar">
      <div className="brand-inline"><span className="brand-mark small">QLDA</span><div><b>QLDA Xây dựng</b><small>Construction Project Management Platform</small></div></div>
      <div className="top-actions"><span className="user-chip"><b>{user?.full_name||user?.username||'User'}</b><small>{user?.role}</small></span>{user?.role==='admin'&&<Link className="link-button ghost-link" href="/admin">Quản trị</Link>}<button className="ghost" onClick={logout}>Đăng xuất</button></div>
    </header>

    <div className="command-layout">
      <aside className="side-nav">
        <p className="side-title">Nghiệp vụ</p>
        {businessGroups.map(g=><div className="side-group" key={g.key}><b>{g.title}</b>{g.modules.map(slug=>{const m=moduleMap[slug];return m?<Link key={slug} href={`/${slug}`}>{m.title}</Link>:null;})}</div>)}
      </aside>

      <section className="content-area">
        <div className="overview-banner"><div><p className="eyebrow">Vận hành dự án</p><h1>Tổng quan điều hành</h1><p>Giao diện và thuật ngữ được chuẩn hóa theo hệ thống QLDA đang vận hành.</p></div><Link className="link-button" href="/dashboard">Mở Dashboard</Link></div>

        {summary&&<div className="kpi-grid production-kpis">
          <div className="kpi"><span>Dự án</span><strong>{summary.projects}</strong></div>
          <div className="kpi"><span>Công việc</span><strong>{summary.tasks?.total??0}</strong><small>{summary.tasks?.overdue??0} quá hạn</small></div>
          <div className="kpi"><span>Hồ sơ chờ</span><strong>{summary.documents_pending??0}</strong></div>
          <div className="kpi"><span>Quality mở</span><strong>{summary.quality_open??0}</strong></div>
          <div className="kpi"><span>VO chờ</span><strong>{summary.changes_pending??0}</strong></div>
          <div className="kpi"><span>Giá trị HĐ</span><strong>{money(summary.contract_value)}</strong></div>
        </div>}

        <form className="panel toolbar wrap global-search" onSubmit={search}><input placeholder="Tìm task, hồ sơ, RFI/NCR/INS, NTCV/NTVL, VO, hợp đồng..." value={q} onChange={e=>setQ(e.target.value)}/><button>Tìm toàn hệ thống</button></form>
        {!!results.length&&<section className="panel"><div className="section-heading"><div><p className="eyebrow">Search</p><h3>Kết quả tìm kiếm</h3></div><span>{results.length} kết quả</span></div><div className="table-wrap"><table><thead><tr><th>Module</th><th>ID</th><th>Nội dung</th></tr></thead><tbody>{results.map((r,i)=><tr key={`${r.module}-${r.record.id}-${i}`}><td>{r.module}</td><td>{r.record.id}</td><td>{r.record.title||r.record.name||r.record.description||r.record.document_no||r.record.number||r.record.contract_no||''}</td></tr>)}</tbody></table></div></section>}

        {businessGroups.map(group=><section className="business-section" key={group.key}><div className="section-heading"><div><p className="eyebrow">{group.title}</p><h2>{group.title}</h2><p>{group.description}</p></div></div><div className="module-grid compact-grid">{group.modules.map((slug,i)=>{const m=moduleMap[slug];if(!m)return null;return <Link className="module-card compact-card" href={`/${m.slug}`} key={m.slug}><span>{String(i+1).padStart(2,'0')}</span><div><h3>{m.title}</h3><p>{m.description}</p></div><b>Mở →</b></Link>;})}</div></section>)}
      </section>
    </div>
  </main>;
}
