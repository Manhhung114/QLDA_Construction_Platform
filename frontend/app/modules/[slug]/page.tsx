import ModuleWorkspace from '@/components/ModuleWorkspace';
export default async function ModulePage({params}:{params:Promise<{slug:string}>}){const {slug}=await params;return <ModuleWorkspace slug={slug}/>}
