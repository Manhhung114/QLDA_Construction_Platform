'use client';

import { useState } from 'react';

export default function AutomationRuleRunner(){
  const [projectId,setProjectId]=useState(''); const [result,setResult]=useState<any>(null); const [error,setError]=useState('');
  const run=async()=>{const qs=projectId?`?project_id=${projectId}`:'';const r=await fetch(`/api/automation/rules/run${qs}`,{method:'POST',headers:{Authorization:`Bearer ${localStorage.getItem('qlda_token')||''}`}});if(!r.ok)return setError(await r.text());setResult(await r.json());setError('');};
  return <section className="panel"><div className="toolbar wrap"><h3>Workflow Rule Engine</h3><input placeholder="Project ID (tùy chọn)" value={projectId} onChange={e=>setProjectId(e.target.value)}/><button onClick={run}>Chạy các rule đã lưu</button></div><p>Thực thi các rule đang bật trong tab Workflow Rules và ghi Approval History + Notification + Audit Log.</p>{error&&<p className="error">{error}</p>}{result&&<pre className="result-box">{JSON.stringify(result,null,2)}</pre>}</section>;
}
