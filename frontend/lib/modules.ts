export type FieldType = 'text' | 'number' | 'date' | 'textarea' | 'select' | 'checkbox' | 'file';
export type FieldDef = {
  key: string;
  label: string;
  type?: FieldType;
  required?: boolean;
  options?: string[];
  optionLabels?: Record<string, string>;
};
export type ModuleDef = {
  slug: string;
  title: string;
  description: string;
  endpoint?: string;
  fields?: FieldDef[];
  secondary?: { label: string; endpoint: string; fields: FieldDef[]; projectScoped?: boolean }[];
  projectScoped?: boolean;
  special?: 'dashboard' | 'automation';
  approvable?: boolean;
  group?: 'overview' | 'commercial' | 'documents' | 'control';
  legacyRefs?: string[];
};

const projectId: FieldDef = { key: 'project_id', label: 'Project ID', type: 'number', required: true };
const statusWorkflow = ['draft','submitted','under_review','approved','rejected','closed'];
const statusLabels: Record<string,string> = {
  planning:'Chuẩn bị', active:'Đang thực hiện', on_hold:'Tạm dừng', completed:'Hoàn thành', closed:'Đóng', cancelled:'Hủy', expired:'Hết hiệu lực',
  draft:'Soạn thảo', submitted:'Đã trình', under_review:'Đang duyệt', approved:'Đã phê duyệt', rejected:'Yêu cầu chỉnh sửa', paid:'Đã thanh toán',
  requested:'Đề nghị', ordered:'Đã đặt hàng', delivered:'Đã giao', sent:'Đã gửi', received:'Đã nhận', open:'Mở',
  todo:'Chưa bắt đầu', in_progress:'Đang thực hiện', review:'Chờ kiểm tra', done:'Hoàn thành', inactive:'Ngưng sử dụng',
  low:'Thấp', medium:'Trung bình', high:'Cao', critical:'Khẩn', actual:'Thực tế', commitment:'Cam kết', forecast:'Dự báo',
  cost:'Chi phí', time:'Thời gian', cost_time:'Chi phí + thời gian'
};
const roleLabels: Record<string,string> = {
  owner:'Chủ sở hữu', project_admin:'Quản trị dự án', manager:'Ban điều hành', reviewer:'Người duyệt', member:'Thành viên', contractor:'Nhà thầu', guest:'Khách'
};
const resourceTypeLabels = {person:'Nhân sự',equipment:'Thiết bị',crew:'Tổ đội'};
const documentTypes = ['RFA','BBHT','NKCT','NTCV','NTVL','KDVT','BBHOP','SHOPDRAWING','ISSUED_DESIGN','UPDATED','AS_BUILT','GENERAL'];
const documentTypeLabels: Record<string,string> = {
  RFA:'RFA - Hồ sơ trình duyệt', BBHT:'Biên bản hiện trường', NKCT:'Nhật ký công trường', NTCV:'Nghiệm thu công việc',
  NTVL:'Nghiệm thu vật liệu đầu vào', KDVT:'Kiểm định vật tư', BBHOP:'Biên bản họp', SHOPDRAWING:'Shopdrawing',
  ISSUED_DESIGN:'Bản vẽ phát hành TKTC', UPDATED:'Bản vẽ cập nhật', AS_BUILT:'Bản vẽ hoàn công', GENERAL:'Hồ sơ khác'
};
const qualityTypes = ['NCR','RFI','INS','NTCV','NTVL','KDVT','MATERIAL','TEST','WORK_INSPECTION'];
const qualityTypeLabels: Record<string,string> = {
  NCR:'NCR - Không phù hợp', RFI:'RFI - Yêu cầu thông tin', INS:'INS - Yêu cầu nghiệm thu', NTCV:'Nghiệm thu công việc',
  NTVL:'Nghiệm thu vật liệu đầu vào', KDVT:'Kiểm định vật tư', MATERIAL:'Phê duyệt vật liệu', TEST:'Thí nghiệm / kiểm định', WORK_INSPECTION:'Kiểm tra công việc'
};

export const modules: ModuleDef[] = [
  {
    slug:'projects', title:'Dự án & Portfolio', endpoint:'projects', group:'overview',
    description:'Dự án, portfolio, thành viên, vai trò và sức khỏe dự án.',
    legacyRefs:['projects'],
    fields:[
      {key:'code',label:'Mã dự án',required:true},{key:'name',label:'Tên dự án',required:true},{key:'description',label:'Mô tả / Ghi chú',type:'textarea'},
      {key:'status',label:'Trạng thái',type:'select',options:['planning','active','on_hold','completed','closed'],optionLabels:statusLabels},
      {key:'start_date',label:'Ngày bắt đầu',type:'date'},{key:'end_date',label:'Ngày kết thúc',type:'date'},
      {key:'budget',label:'Ngân sách',type:'number'},{key:'manager',label:'Quản lý dự án'}
    ],
    secondary:[{label:'Thành viên dự án',endpoint:'project-members',projectScoped:true,fields:[projectId,{key:'user_id',label:'User ID',type:'number',required:true},{key:'role',label:'Vai trò',type:'select',options:['owner','project_admin','manager','reviewer','member','contractor','guest'],optionLabels:roleLabels},{key:'can_approve',label:'Có quyền duyệt',type:'checkbox'}]}]
  },
  {
    slug:'tasks', title:'Công việc & WBS', endpoint:'tasks', projectScoped:true, group:'overview',
    description:'WBS, công việc, checklist, dependency FS/SS/FF/SF, ưu tiên và tiến độ.',
    legacyRefs:['tasks'],
    fields:[projectId,{key:'wbs_id',label:'WBS ID',type:'number'},{key:'title',label:'Công việc',required:true},{key:'description',label:'Mô tả',type:'textarea'},
      {key:'assignee',label:'Phụ trách'},{key:'status',label:'Trạng thái',type:'select',options:['todo','in_progress','review','done','closed'],optionLabels:statusLabels},
      {key:'priority',label:'Ưu tiên',type:'select',options:['low','medium','high','critical'],optionLabels:statusLabels},{key:'start_date',label:'Bắt đầu',type:'date'},
      {key:'due_date',label:'Kết thúc / Deadline',type:'date'},{key:'baseline_start',label:'Baseline bắt đầu',type:'date'},{key:'baseline_due',label:'Baseline kết thúc',type:'date'},
      {key:'progress',label:'% hoàn thành',type:'number'}],
    secondary:[
      {label:'WBS',endpoint:'wbs',fields:[projectId,{key:'code',label:'Mã WBS',required:true},{key:'name',label:'Tên WBS',required:true},{key:'parent_id',label:'WBS cha',type:'number'},{key:'weight',label:'Trọng số',type:'number'},{key:'progress',label:'Tiến độ %',type:'number'}]},
      {label:'Quan hệ công việc',endpoint:'task-dependencies',fields:[projectId,{key:'task_id',label:'Task ID',type:'number',required:true},{key:'predecessor_id',label:'Công việc trước',type:'number',required:true},{key:'dependency_type',label:'Kiểu liên kết',type:'select',options:['FS','SS','FF','SF']},{key:'lag_days',label:'Độ trễ (ngày)',type:'number'}]},
      {label:'Checklist',endpoint:'checklists',fields:[{key:'task_id',label:'Task ID',type:'number',required:true},{key:'text',label:'Nội dung',required:true},{key:'is_done',label:'Hoàn thành',type:'checkbox'},{key:'sort_order',label:'Thứ tự',type:'number'}]}
    ]
  },
  {
    slug:'schedule', title:'Tiến độ', endpoint:'schedule', projectScoped:true, group:'overview',
    description:'Kế hoạch/thực tế, baseline, milestone, predecessor, Gantt và đường găng.',
    legacyRefs:['tasks','schedule'],
    fields:[projectId,{key:'activity_code',label:'Mã công việc',required:true},{key:'name',label:'Tên công việc',required:true},{key:'planned_start',label:'KH bắt đầu',type:'date'},
      {key:'planned_end',label:'KH kết thúc',type:'date'},{key:'actual_start',label:'TT bắt đầu',type:'date'},{key:'actual_end',label:'TT kết thúc',type:'date'},
      {key:'progress',label:'Tiến độ %',type:'number'},{key:'critical',label:'Đường găng',type:'checkbox'},{key:'milestone',label:'Milestone',type:'checkbox'},{key:'predecessor_ids',label:'Công việc trước'}]
  },
  {
    slug:'resources', title:'Nguồn lực & Thời gian', endpoint:'resources', projectScoped:true, group:'overview',
    description:'Nhân lực, thiết bị, tổ đội, phân bổ task, workload và timesheet.',
    fields:[projectId,{key:'name',label:'Tên nguồn lực',required:true},{key:'resource_type',label:'Loại',type:'select',options:['person','equipment','crew'],optionLabels:resourceTypeLabels},{key:'capacity_hours',label:'Giờ/ngày',type:'number'},{key:'cost_rate',label:'Đơn giá/giờ',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:['active','inactive'],optionLabels:statusLabels}],
    secondary:[
      {label:'Phân bổ',endpoint:'resource-assignments',fields:[projectId,{key:'resource_id',label:'Resource ID',type:'number',required:true},{key:'task_id',label:'Task ID',type:'number',required:true},{key:'allocation_percent',label:'Phân bổ %',type:'number'},{key:'planned_hours',label:'Giờ kế hoạch',type:'number'}]},
      {label:'Timesheet',endpoint:'timesheets',fields:[projectId,{key:'resource_id',label:'Resource ID',type:'number',required:true},{key:'task_id',label:'Task ID',type:'number'},{key:'work_date',label:'Ngày',type:'date',required:true},{key:'hours',label:'Giờ',type:'number'},{key:'note',label:'Ghi chú',type:'textarea'}]}
    ]
  },
  {
    slug:'costs', title:'BOQ & Kiểm soát chi phí', endpoint:'boq', projectScoped:true, group:'commercial',
    description:'BOQ, ngân sách, cam kết, thực tế, dự báo và variance.',
    legacyRefs:['cost_budgets','BOQ','IPC'],
    fields:[projectId,{key:'item_code',label:'Mã BOQ',required:true},{key:'description',label:'Mô tả',type:'textarea',required:true},{key:'unit',label:'Đơn vị'},
      {key:'quantity',label:'Khối lượng',type:'number'},{key:'unit_rate',label:'Đơn giá',type:'number'},{key:'budget_amount',label:'Ngân sách',type:'number'},
      {key:'actual_qty',label:'KL thực tế',type:'number'},{key:'actual_amount',label:'Chi phí thực tế',type:'number'}],
    secondary:[
      {label:'Phiên bản ngân sách',endpoint:'budget-versions',fields:[projectId,{key:'version',label:'Phiên bản',required:true},{key:'description',label:'Mô tả',type:'textarea'},{key:'total_budget',label:'Tổng ngân sách',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:['draft','submitted','approved','rejected'],optionLabels:statusLabels},{key:'effective_date',label:'Ngày hiệu lực',type:'date'}]},
      {label:'Chi phí',endpoint:'costs',fields:[projectId,{key:'boq_item_id',label:'BOQ ID',type:'number'},{key:'cost_type',label:'Loại chi phí',type:'select',options:['actual','commitment','forecast'],optionLabels:statusLabels},{key:'description',label:'Nội dung',required:true},{key:'amount',label:'Giá trị',type:'number'},{key:'entry_date',label:'Ngày',type:'date'}]}
    ]
  },
  {
    slug:'contracts', title:'Hợp đồng & Mua sắm', endpoint:'contracts', projectScoped:true, approvable:true, group:'commercial',
    description:'Hợp đồng, thời hạn, payment certificate, nhà cung cấp và procurement.',
    legacyRefs:['payment_tracking','procurement_schedule'],
    fields:[projectId,{key:'contract_no',label:'Số hợp đồng',required:true},{key:'contractor',label:'Nhà thầu',required:true},{key:'scope',label:'Phạm vi',type:'textarea'},
      {key:'contract_value',label:'Giá trị hợp đồng',type:'number'},{key:'start_date',label:'Ngày bắt đầu',type:'date'},{key:'duration_days',label:'Thời gian thi công (ngày)',type:'number'},
      {key:'end_date',label:'Ngày hết hiệu lực',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['draft','active','expired','closed','cancelled'],optionLabels:statusLabels}],
    secondary:[
      {label:'Thanh toán / IPC',endpoint:'payments',fields:[projectId,{key:'contract_id',label:'Contract ID',type:'number',required:true},{key:'certificate_no',label:'Số thanh toán',required:true},{key:'period_from',label:'Từ ngày',type:'date'},{key:'period_to',label:'Đến ngày',type:'date'},{key:'gross_amount',label:'Giá trị xác nhận',type:'number'},{key:'retention_amount',label:'Giữ lại',type:'number'},{key:'net_amount',label:'Giá trị thanh toán',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:['draft','submitted','under_review','approved','rejected','paid'],optionLabels:statusLabels}]},
      {label:'Procurement',endpoint:'procurement',fields:[projectId,{key:'po_no',label:'Mã PO / Đề nghị',required:true},{key:'vendor',label:'Nhà cung cấp',required:true},{key:'description',label:'Nội dung',type:'textarea'},{key:'amount',label:'Giá trị',type:'number'},{key:'expected_date',label:'Ngày dự kiến',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['requested','approved','ordered','delivered','closed','cancelled'],optionLabels:statusLabels}]}
    ]
  },
  {
    slug:'documents', title:'Quản lý hồ sơ & Bản vẽ', endpoint:'documents', projectScoped:true, approvable:true, group:'documents',
    description:'Hồ sơ, bản vẽ, revision, transmittal, file và lịch sử phê duyệt.',
    legacyRefs:['documents','drawings','document_attachments','drawing_attachments','approval_workflows','approval_history'],
    fields:[projectId,{key:'document_no',label:'Số / Mã hồ sơ',required:true},{key:'title',label:'Tên hồ sơ',required:true},{key:'category',label:'Loại hồ sơ',type:'select',options:documentTypes,optionLabels:documentTypeLabels},{key:'discipline',label:'Bộ môn'},{key:'current_revision',label:'Revision'},{key:'status',label:'Trạng thái',type:'select',options:statusWorkflow,optionLabels:statusLabels},{key:'file_url',label:'File đính kèm',type:'file'}],
    secondary:[
      {label:'Revision',endpoint:'document-revisions',fields:[{key:'document_id',label:'Document ID',type:'number',required:true},{key:'revision',label:'Revision',required:true},{key:'file_url',label:'File',type:'file'},{key:'submitted_by',label:'Người trình'},{key:'reviewed_by',label:'Người kiểm tra'},{key:'approved_by',label:'Người duyệt'},{key:'approval_date',label:'Ngày duyệt',type:'date'},{key:'status',label:'Trạng thái',type:'select',options:['submitted','under_review','rejected','approved'],optionLabels:statusLabels}]},
      {label:'Transmittal',endpoint:'transmittals',fields:[projectId,{key:'transmittal_no',label:'Mã transmittal',required:true},{key:'subject',label:'Chủ đề',required:true},{key:'sender',label:'Người gửi'},{key:'recipient',label:'Người nhận'},{key:'sent_date',label:'Ngày gửi',type:'date'},{key:'document_ids',label:'Danh sách Document ID',type:'textarea'},{key:'status',label:'Trạng thái',type:'select',options:['draft','sent','received','closed'],optionLabels:statusLabels}]},
      {label:'Lịch sử phê duyệt',endpoint:'approval-actions',projectScoped:true,fields:[]}
    ]
  },
  {
    slug:'quality', title:'Chất lượng / RFI / NCR / INS', endpoint:'quality', projectScoped:true, approvable:true, group:'documents',
    description:'RFI, NCR, INS, nghiệm thu công việc, vật liệu đầu vào và kiểm định vật tư.',
    legacyRefs:['NCR','RFI','NTCV','NTVL','KDVT'],
    fields:[projectId,{key:'item_type',label:'Loại hồ sơ',type:'select',options:qualityTypes,optionLabels:qualityTypeLabels},{key:'number',label:'Mã hồ sơ',required:true},{key:'title',label:'Nội dung / Hạng mục',required:true},{key:'description',label:'Mô tả / Ý kiến',type:'textarea'},{key:'status',label:'Trạng thái',type:'select',options:['open','submitted','under_review','rejected','approved','closed'],optionLabels:statusLabels},{key:'raised_by',label:'Người / Đơn vị trình'},{key:'assigned_to',label:'Người / Đơn vị xử lý'},{key:'due_date',label:'Hạn xử lý / nghiệm thu',type:'date'}],
    secondary:[{label:'Lịch sử phê duyệt',endpoint:'approval-actions',projectScoped:true,fields:[]}]
  },
  {
    slug:'changes', title:'Phát sinh / VO / Claim', endpoint:'changes', projectScoped:true, approvable:true, group:'commercial',
    description:'VO, phát sinh, claim, tác động chi phí và tiến độ.',
    legacyRefs:['cost_variations','VO'],
    fields:[projectId,{key:'vo_no',label:'Mã VO / Phát sinh',required:true},{key:'title',label:'Tiêu đề',required:true},{key:'reason',label:'Lý do / Cơ sở',type:'textarea'},{key:'cost_impact',label:'Tác động chi phí',type:'number'},{key:'time_impact_days',label:'Tác động tiến độ (ngày)',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:statusWorkflow,optionLabels:statusLabels},{key:'submitted_date',label:'Ngày trình',type:'date'},{key:'approved_date',label:'Ngày duyệt',type:'date'}],
    secondary:[{label:'Claim',endpoint:'claims',fields:[projectId,{key:'contract_id',label:'Contract ID',type:'number'},{key:'claim_no',label:'Mã Claim',required:true},{key:'title',label:'Tiêu đề',required:true},{key:'claim_type',label:'Loại',type:'select',options:['cost','time','cost_time'],optionLabels:statusLabels},{key:'amount',label:'Giá trị',type:'number'},{key:'extension_days',label:'Gia hạn (ngày)',type:'number'},{key:'status',label:'Trạng thái',type:'select',options:statusWorkflow,optionLabels:statusLabels},{key:'description',label:'Mô tả',type:'textarea'}]}]
  },
  {
    slug:'collaboration', title:'Trao đổi & Thông báo', endpoint:'comments', projectScoped:true, group:'control',
    description:'Trao đổi theo đối tượng, thông báo, lịch sử thao tác và phối hợp nội bộ.',
    fields:[projectId,{key:'entity_type',label:'Đối tượng',required:true},{key:'entity_id',label:'ID đối tượng',type:'number',required:true},{key:'author',label:'Người bình luận'},{key:'body',label:'Nội dung',type:'textarea',required:true}],
    secondary:[{label:'Thông báo',endpoint:'notifications',fields:[{key:'user_id',label:'User ID',type:'number'},{key:'project_id',label:'Project ID',type:'number'},{key:'title',label:'Tiêu đề',required:true},{key:'message',label:'Thông báo',type:'textarea',required:true},{key:'is_read',label:'Đã đọc',type:'checkbox'}]}]
  },
  {slug:'dashboard',title:'Dashboard & BI',description:'KPI dự án, chi phí, hồ sơ, chất lượng, portfolio và drill-down.',special:'dashboard',group:'control'},
  {
    slug:'automation', title:'Automation & AI', endpoint:'workflow-rules', projectScoped:true, special:'automation', group:'control',
    description:'Workflow rules, cảnh báo tự động, audit và risk summary.',
    fields:[{key:'project_id',label:'Project ID',type:'number'},{key:'module',label:'Module',required:true},{key:'trigger_status',label:'Từ trạng thái',required:true},{key:'action_status',label:'Sang trạng thái',required:true},{key:'assign_to',label:'Gán cho'},{key:'enabled',label:'Kích hoạt',type:'checkbox'}],
    secondary:[{label:'Audit log',endpoint:'audit-logs',fields:[]}]
  }
];

export const moduleBySlug = (slug: string) => modules.find(m => m.slug === slug);
