'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const headers = () => ({'Content-Type':'application/json',Authorization:`Bearer ${localStorage.getItem('qlda_token') || ''}`});

export default function AdminPage(){
  const [users,setUsers]=useState<any[]>([]); const [error,setError]=useState('');
  const [form,setForm]=useState({username:'',password:'',full_name:'',email:'',role:'member'});
  const load=async()=>{const r=await fetch('/api/auth/users',{headers:headers()});if(!r.ok)return setError(await r.text());setUsers(await r.json());};
  useEffect(()=>{load();},[]);
  const create=async(e:React.FormEvent)=>{e.preventDefault();setError('');const r=await fetch('/api/auth/users',{method:'POST',headers:headers(),body:JSON.stringify(form)});if(!r.ok)return setError(await r.text());setForm({username:'',password:'',full_name:'',email:'',role:'member'});await load();};
  return <main className="shell"><div className="toolbar wrap"><Link className="link-button ghost-link" href="/">← Tổng quan</Link><h2>Quản trị người dùng</h2></div>{error&&<p className="error">{error}</p>}
    <form className="panel form-grid" onSubmit={create}><h3>Tạo tài khoản</h3><label><span>Username</span><input required value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></label><label><span>Mật khẩu (≥10 ký tự)</span><input required type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label><label><span>Họ tên</span><input value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></label><label><span>Email</span><input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><label><span>System role</span><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})}><option>admin</option><option>manager</option><option>member</option><option>guest</option></select></label><div className="wide"><button>Tạo tài khoản</button></div></form>
    <div className="table-wrap"><table><thead><tr><th>ID</th><th>Username</th><th>Họ tên</th><th>Email</th><th>Role</th><th>Active</th></tr></thead><tbody>{users.map(u=><tr key={u.id}><td>{u.id}</td><td>{u.username}</td><td>{u.full_name}</td><td>{u.email}</td><td>{u.role}</td><td>{u.is_active?'✓':'—'}</td></tr>)}</tbody></table></div>
  </main>;
}
