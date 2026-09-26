'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { modules } from '@/lib/modules';

export default function Home(){
  const [token,setToken]=useState(''); const [username,setUsername]=useState('admin'); const [password,setPassword]=useState('');
  const [user,setUser]=useState<any>(null); const [error,setError]=useState(''); const [q,setQ]=useState(''); const [results,setResults]=useState<any[]>([]);
  useEffect(()=>{const saved=localStorage.getItem('qlda_token')||'';setToken(saved);if(saved)fetch('/api/auth/me',{headers:{Authorization:`Bearer ${saved}`}}).then(r=>r.ok?r.json():null).then(setUser);},[]);
  const login=async(e:React.FormEvent)=>{e.preventDefault();setError('');const res=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});if(!res.ok)return setError('Không đăng nhập được. Kiểm tra tài khoản/mật khẩu.');const data=await res.json();localStorage.setItem('qlda_token',data.access_token);setToken(data.access_token);setUser(data.user);setPassword('');};
  const logout=()=>{localStorage.removeItem('qlda_token');setToken('');setUser(null);setResults([]);};
  const search=async(e:React.FormEvent)=>{e.preventDefault();if(q.trim().length<2)return;const r=await fetch(`/api/search?q=${encodeURIComponent(q)}`,{headers:{Authorization:`Bearer ${localStorage.getItem('qlda_token')||''}`}});if(r.ok)setResults(await r.json());};
  if(!token)return <main className="login-page"><form className="login-card" onSubmit={login}><p className="eyebrow">Construction Project Management</p><h1>QLDA Platform</h1><p>Đăng nhập nền tảng quản lý dự án xây dựng 12 module.</p><label>Tài khoản<input value={username} onChange={e=>setUsername(e.target.value)}/></label><label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)}/></label>{error&&<p className="error">{error}</p>}<button>Đăng nhập</button></form></main>;
  return <main className="shell">
    <header className="hero"><div><p className="eyebrow">QLDA Construction Platform · V2 Production Beta</p><h1>Điều hành dự án xây dựng trên một nền tảng</h1><p>12 module, workflow phê duyệt, RBAC theo dự án, audit trail, dashboard và automation.</p></div><div className="user-box"><b>{user?.full_name||user?.username||'User'}</b><small>{user?.role}</small>{user?.role==='admin'&&<Link className="link-button" href="/admin">Quản trị user</Link>}<button className="ghost" onClick={logout}>Đăng xuất</button></div></header>
    <form className="panel toolbar wrap" onSubmit={search}><input placeholder="Tìm task, hồ sơ, RFI/NCR/INS, VO, hợp đồng..." value={q} onChange={e=>setQ(e.target.value)}/><button>Tìm toàn hệ thống</button></form>
    {!!results.length&&<section className="panel"><h3>Kết quả tìm kiếm</h3><div className="table-wrap"><table><thead><tr><th>Module</th><th>ID</th><th>Nội dung</th></tr></thead><tbody>{results.map((r,i)=><tr key={`${r.module}-${r.record.id}-${i}`}><td>{r.module}</td><td>{r.record.id}</td><td>{r.record.title||r.record.name||r.record.description||r.record.document_no||r.record.number||r.record.contract_no||''}</td></tr>)}</tbody></table></div></section>}
    <section className="module-grid">{modules.map((m,i)=><Link className="module-card" href={`/${m.slug}`} key={m.slug}><span>{String(i+1).padStart(2,'0')}</span><h2>{m.title}</h2><p>{m.description}</p><b>Mở module →</b></Link>)}</section>
  </main>;
}
