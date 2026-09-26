'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { modules } from '@/lib/modules';

export default function Home() {
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem('qlda_token') || '';
    setToken(saved);
    if (saved) fetch('/api/auth/me',{headers:{Authorization:`Bearer ${saved}`}}).then(r=>r.ok?r.json():null).then(setUser);
  }, []);

  const login = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    const res = await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
    if (!res.ok) return setError('Không đăng nhập được. Kiểm tra tài khoản/mật khẩu.');
    const data = await res.json(); localStorage.setItem('qlda_token',data.access_token); setToken(data.access_token); setUser(data.user); setPassword('');
  };

  const logout = () => { localStorage.removeItem('qlda_token'); setToken(''); setUser(null); };

  if (!token) return <main className="login-page"><form className="login-card" onSubmit={login}><p className="eyebrow">Construction Project Management</p><h1>QLDA Platform</h1><p>Đăng nhập vào nền tảng 12 module.</p><label>Tài khoản<input value={username} onChange={e=>setUsername(e.target.value)} /></label><label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></label>{error&&<p className="error">{error}</p>}<button>Đăng nhập</button></form></main>;

  return <main className="shell">
    <header className="hero"><div><p className="eyebrow">QLDA Construction Platform · V1</p><h1>Điều hành dự án xây dựng trên một nền tảng</h1><p>12 module dùng chung dữ liệu dự án, workflow, audit trail và dashboard.</p></div><div className="user-box"><b>{user?.full_name || user?.username || 'User'}</b><small>{user?.role}</small><button className="ghost" onClick={logout}>Đăng xuất</button></div></header>
    <section className="module-grid">{modules.map((m,i)=><Link className="module-card" href={`/${m.slug}`} key={m.slug}><span>{String(i+1).padStart(2,'0')}</span><h2>{m.title}</h2><p>{m.description}</p><b>Mở module →</b></Link>)}</section>
  </main>;
}
