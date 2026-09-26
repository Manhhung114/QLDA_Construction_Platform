export type FieldType = 'text' | 'number' | 'date' | 'textarea' | 'select' | 'checkbox' | 'file';

export type FieldDef = {
  key: string;
  label: string;
  type?: FieldType;
  required?: boolean;
  options?: string[];
};

export type ModuleDef = {
  slug: string;
  title: string;
  description: string;
  endpoint?: string;
  secondary?: { label: string; endpoint: string; fields: FieldDef[] }[];
  fields?: FieldDef[];
  projectScoped?: boolean;
  special?: 'dashboard' | 'automation';
};

const projectId: FieldDef = { key: 'project_id', label: 'Project ID', type: 'number', required: true };

export const modules: ModuleDef[] = [
  {
    slug: 'projects', title: 'Project & Portfolio', endpoint: 'projects',
    description: 'Danh mục dự án, ngân sách, thời gian, trạng thái và portfolio.',
    fields: [
      { key: 'code', label: 'Mã dự án', required: true }, { key: 'name', label: 'Tên dự án', required: true },
      { key: 'description', label: 'Mô tả', type: 'textarea' }, { key: 'status', label: 'Trạng thái', type: 'select', options: ['planning','active','on_hold','completed','closed'] },
      { key: 'start_date', label: 'Ngày bắt đầu', type: 'date' }, { key: 'end_date', label: 'Ngày kết thúc', type: 'date' },
      { key: 'budget', label: 'Ngân sách', type: 'number' }, { key: 'manager', label: 'Quản lý dự án' }
    ]
  },
  {
    slug: 'tasks', title: 'Task & WBS', endpoint: 'tasks', projectScoped: true,
    description: 'WBS, task, người phụ trách, ưu tiên, dependency và tiến độ.',
    fields: [projectId, { key:'wbs_id',label:'WBS ID',type:'number' }, { key:'title',label:'Công việc',required:true },
      { key:'description',label:'Mô tả',type:'textarea' }, { key:'assignee',label:'Phụ trách' },
      { key:'status',label:'Trạng thái',type:'select',options:['todo','in_progress','review','done','closed'] },
      { key:'priority',label:'Ưu tiên',type:'select',options:['low','medium','high','critical'] },
      { key:'start_date',label:'Bắt đầu',type:'date' }, { key:'due_date',label:'Deadline',type:'date' },
      { key:'baseline_start',label:'Baseline start',type:'date' }, { key:'baseline_due',label:'Baseline due',type:'date' },
      { key:'progress',label:'% hoàn thành',type:'number' }, { key:'predecessor_id',label:'Task trước',type:'number' }],
    secondary: [{ label:'WBS', endpoint:'wbs', fields:[projectId,{key:'code',label:'Mã WBS',required:true},{key:'name',label:'Tên WBS',required:true},{key:'parent_id',label:'WBS cha',type:'number'},{key:'weight',label:'Trọng số',type:'number'},{key:'progress',label:'Tiến độ %',type:'number'}] }]
  },
  {
    slug:'schedule', title:'Schedule', endpoint:'schedule', projectScoped:true,
    description:'Tiến độ kế hoạch/thực tế, milestone, predecessor và critical path flag.',
    fields:[projectId,{key:'activity_code',label:'Mã công việc',required:true},{key:'name',label:'Tên công việc',required:true},{key:'planned_start',label:'Kế hoạch bắt đầu',type:'date'},{key:'planned_end',label:'Kế hoạch kết thúc',type:'date'},{key:'actual_start',label:'Thực tế bắt đầu',type:'date'},{key:'actual_end',label:'Thực tế kết thúc',type:'date'},{key:'progress',label:'Tiến độ %',type:'number'},{key:'critical',label:'Critical',type:'checkbox'},{key:'milestone',label:'Milestone',type:'checkbox'},{key:'predecessor_ids',label:'Predecessor IDs'}]
  },
  {
    slug:'resources', title:'Resource & Time', endpoint:'resources', projectScoped:true,
    description:'Nguồn lực, công suất, đơn giá và timesheet.',
    fields:[projectId,{key:'name',label:'Tên nguồn lực',required:true},{key:'resource_type',label:'Loại',type:'select',options:['person','equipment','crew']},{key:'capacity_hours',label:'Giờ/ngày',type:'number'},{key:'cost_rate',label:'Đơn giá/giờ',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:['active','inactive']}],
    secondary:[{label:'Timesheet',endpoint:'timesheets',fields:[projectId,{key:'resource_id',label:'Resource ID',type:'number',required:true},{key:'task_id',label:'Task ID',type:'number'},{key:'work_date',label:'Ngày',type:'date',required:true},{key:'hours',label:'Giờ',type:'number'},{key:'note',label:'Ghi chú',type:'textarea'}]}]
  },
  {
    slug:'costs', title:'BOQ & Cost Control', endpoint:'boq', projectScoped:true,
    description:'BOQ, ngân sách, khối lượng thực tế, actual cost và variance.',
    fields:[projectId,{key:'item_code',label:'Mã BOQ',required:true},{key:'description',label:'Mô tả',type:'textarea',required:true},{key:'unit',label:'Đơn vị'},{key:'quantity',label:'Khối lượng',type:'number'},{key:'unit_rate',label:'Đơn giá',type:'number'},{key:'budget_amount',label:'Ngân sách',type:'number'},{key:'actual_qty',label:'KL thực tế',type:'number'},{key:'actual_amount',label:'Chi phí thực tế',type:'number'}],
    secondary:[{label:'Cost entries',endpoint:'costs',fields:[projectId,{key:'boq_item_id',label:'BOQ ID',type:'number'},{key:'cost_type',label:'Loại chi phí',type:'select',options:['actual','commitment','forecast']},{key:'description',label:'Nội dung',required:true},{key:'amount',label:'Giá trị',type:'number'},{key:'entry_date',label:'Ngày',type:'date'}]}]
  },
  {
    slug:'contracts', title:'Contract & Procurement', endpoint:'contracts', projectScoped:true,
    description:'Hợp đồng, thời hạn tự tính, nhà thầu và mua sắm.',
    fields:[projectId,{key:'contract_no',label:'Số hợp đồng',required:true},{key:'contractor',label:'Nhà thầu',required:true},{key:'scope',label:'Phạm vi',type:'textarea'},{key:'contract_value',label:'Giá trị',type:'number'},{key:'start_date',label:'Ngày bắt đầu',type:'date'},{key:'duration_days',label:'Thời gian thi công (ngày)',type:'number'},{key:'end_date',label:'Ngày hết hiệu lực',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['draft','active','expired','closed','cancelled']}],
    secondary:[{label:'Procurement',endpoint:'procurement',fields:[projectId,{key:'po_no',label:'PO No.',required:true},{key:'vendor',label:'Nhà cung cấp',required:true},{key:'description',label:'Nội dung',type:'textarea'},{key:'amount',label:'Giá trị',type:'number'},{key:'expected_date',label:'Ngày dự kiến',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['requested','approved','ordered','delivered','closed']}]}]
  },
  {
    slug:'documents', title:'Document Control', endpoint:'documents', projectScoped:true,
    description:'Hồ sơ, bản vẽ, revision, file đính kèm và trạng thái phê duyệt.',
    fields:[projectId,{key:'document_no',label:'Số hồ sơ',required:true},{key:'title',label:'Tên hồ sơ',required:true},{key:'category',label:'Loại hồ sơ',type:'select',options:['drawing','method_statement','material','inspection','report','general']},{key:'discipline',label:'Bộ môn'},{key:'current_revision',label:'Revision'},{key:'status',label:'Trạng thái',type:'select',options:['draft','submitted','under_review','rejected','approved','closed']},{key:'file_url',label:'File',type:'file'}],
    secondary:[{label:'Revisions',endpoint:'document-revisions',fields:[{key:'document_id',label:'Document ID',type:'number',required:true},{key:'revision',label:'Revision',required:true},{key:'file_url',label:'File',type:'file'},{key:'submitted_by',label:'Người nộp'},{key:'reviewed_by',label:'Người kiểm tra'},{key:'approved_by',label:'Người duyệt'},{key:'approval_date',label:'Ngày duyệt',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['submitted','under_review','rejected','approved']}]}]
  },
  {
    slug:'quality', title:'Quality / RFI / NCR / INS', endpoint:'quality', projectScoped:true,
    description:'RFI, NCR, INS, vật liệu đầu vào, kiểm định và nghiệm thu.',
    fields:[projectId,{key:'item_type',label:'Loại',type:'select',options:['RFI','NCR','INS','MATERIAL','TEST','WORK_INSPECTION']},{key:'number',label:'Số hồ sơ',required:true},{key:'title',label:'Tiêu đề',required:true},{key:'description',label:'Nội dung',type:'textarea'},{key:'status',label:'Trạng thái',type:'select',options:['open','submitted','under_review','rejected','approved','closed']},{key:'raised_by',label:'Người tạo'},{key:'assigned_to',label:'Người xử lý'},{key:'due_date',label:'Hạn xử lý',type:'date'}]
  },
  {
    slug:'changes', title:'Change Management', endpoint:'changes', projectScoped:true,
    description:'VO, phát sinh, claim, tác động chi phí và tiến độ.',
    fields:[projectId,{key:'vo_no',label:'VO No.',required:true},{key:'title',label:'Tiêu đề',required:true},{key:'reason',label:'Lý do',type:'textarea'},{key:'cost_impact',label:'Tác động chi phí',type:'number'},{key:'time_impact_days',label:'Tác động ngày',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:['draft','submitted','under_review','approved','rejected','closed']},{key:'submitted_date',label:'Ngày trình',type:'date'},{key:'approved_date',label:'Ngày duyệt',type:'date'}]
  },
  {
    slug:'collaboration', title:'Collaboration', endpoint:'comments', projectScoped:true,
    description:'Trao đổi theo đối tượng, thông báo và lịch sử phối hợp.',
    fields:[projectId,{key:'entity_type',label:'Đối tượng',required:true},{key:'entity_id',label:'ID đối tượng',type:'number',required:true},{key:'author',label:'Người bình luận',required:true},{key:'body',label:'Nội dung',type:'textarea',required:true}],
    secondary:[{label:'Notifications',endpoint:'notifications',fields:[{key:'user_id',label:'User ID',type:'number'},{key:'project_id',label:'Project ID',type:'number'},{key:'title',label:'Tiêu đề',required:true},{key:'message',label:'Thông báo',type:'textarea',required:true},{key:'is_read',label:'Đã đọc',type:'checkbox'}]}]
  },
  { slug:'dashboard', title:'Dashboard & BI', description:'Sức khỏe dự án, tiến độ, chi phí, hồ sơ và portfolio.', special:'dashboard' },
  {
    slug:'automation', title:'Automation & AI', endpoint:'workflow-rules', projectScoped:true, special:'automation',
    description:'Workflow rules, cảnh báo tự động và phân tích rủi ro dự án.',
    fields:[{key:'project_id',label:'Project ID',type:'number'},{key:'module',label:'Module',required:true},{key:'trigger_status',label:'Từ trạng thái',required:true},{key:'action_status',label:'Sang trạng thái',required:true},{key:'assign_to',label:'Gán cho'},{key:'enabled',label:'Kích hoạt',type:'checkbox'}]
  }
];

export const moduleBySlug = (slug: string) => modules.find((m) => m.slug === slug);
