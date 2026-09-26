'use client';
import { useParams } from 'next/navigation';
import ModuleWorkspace from '@/components/ModuleWorkspace';
import { moduleBySlug } from '@/lib/modules';

export default function ModulePage() {
  const params = useParams<{ module: string }>();
  const module = moduleBySlug(params.module);
  if (!module) return <main className="shell"><div className="panel"><h1>Không tìm thấy module</h1></div></main>;
  return <main className="shell"><header className="page-head"><div><p className="eyebrow">QLDA Construction Platform</p><h1>{module.title}</h1><p>{module.description}</p></div></header><ModuleWorkspace module={module} /></main>;
}
