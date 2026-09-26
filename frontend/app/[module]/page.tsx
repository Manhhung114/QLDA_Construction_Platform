'use client';

import { useParams } from 'next/navigation';
import AutomationRuleRunner from '@/components/AutomationRuleRunner';
import ModuleWorkspace from '@/components/ModuleWorkspace';
import { GanttCPM, ImportPanel, KanbanBoard, ProjectCalendar } from '@/components/ProjectVisuals';
import { moduleBySlug } from '@/lib/modules';

const importable = new Set(['tasks','schedule','resources','costs','contracts','documents','quality','changes']);

export default function ModulePage(){
  const params=useParams<{module:string}>();
  const module=moduleBySlug(params.module);
  if(!module)return <main className="shell"><div className="panel"><h1>Không tìm thấy module</h1></div></main>;
  return <main className="shell">
    <header className="page-head"><div><p className="eyebrow">QLDA Construction Platform · V2</p><h1>{module.title}</h1><p>{module.description}</p></div></header>
    <ModuleWorkspace module={module}/>
    {module.slug==='tasks'&&<><KanbanBoard/><ProjectCalendar/></>}
    {module.slug==='schedule'&&<><GanttCPM/><ProjectCalendar/></>}
    {module.slug==='automation'&&<AutomationRuleRunner/>}
    {importable.has(module.slug)&&module.endpoint&&<ImportPanel module={module.endpoint} projectScoped={module.projectScoped}/>} 
  </main>;
}
